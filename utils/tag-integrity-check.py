#!/usr/bin/env python
"""Check that all repo tags match what we expect.

If a student has manipulated a course tab, then we will find it and display
it prominently.

Author: Aidan McNay
Date: September 21st, 2024
"""

import argparse
import github
import pydoc
import sys
from typing import Optional

from github_steps import _org
from google_steps import _sheets
from google_steps.spreadsheet_storer import SpreadsheetStorer
from records.tag_record import TagRecords, get_tag_headers

# ------------------------------------------------------------------------
# Arguments
# ------------------------------------------------------------------------

info_present = "-i" in sys.argv or "--info" in sys.argv

parser = argparse.ArgumentParser(
    description=(
        "A simple script to check that lab tags haven't been manipulated"
    ),
)

parser.add_argument(
    "--sheet-id",
    help="The ID of the Google Sheet where tag records are stored",
    metavar="SHEET_ID",
    required=not info_present,
)
parser.add_argument(
    "--tab",
    help="The tab on the Google Sheet to get tag records from",
    metavar="TAB",
    required=not info_present,
)
parser.add_argument(
    "--lab",
    help="The lab to check the tags for",
    metavar="LAB",
    required=not info_present,
)
parser.add_argument(
    "-n",
    "--no-color",
    help="Don't print in color (use for file logging)",
    action="store_true",
)
parser.add_argument(
    "-i",
    "--info",
    help="Print out verbose information about the program and exit",
    action="store_true",
)

# Parse the arguments
args = parser.parse_args()

# ------------------------------------------------------------------------
# Info
# ------------------------------------------------------------------------

info = f"""
{parser.format_usage()}

`tag-integrity-check` is used to check that all staff-tagged repos are
intact. The repo tags are checked against stored checksums to ensure that
no manipulation has occurred since the course staff tagged them.

Arguments:
 - `sheet-id`: The ID of the Google Sheet where tag records are stored
 - `tab`: The tab on the Google Sheet to get tag records from
 - `lab`: The lab to check the tags for

Assumptions:

`tag-integrity-check` takes the expected tags from a Google Sheet, and
assumes that the sheet represents a collection of `TagRecords` as stored
by a `SpreadsheetStorer`. Using those records, the script will check not
only that the tags are present, but that the hashes of the tag and the
commit that it points to are as expected.
"""

if args.info:
    pydoc.pager(info)
    exit(0)

# ------------------------------------------------------------------------
# Printing functions
# ------------------------------------------------------------------------

if args.no_color:
    RED = ""
    GREEN = ""
    RESET = ""
else:
    RED = "\033[1;31m"
    GREEN = "\033[1;32m"
    RESET = "\033[0m"


def print_good_tag(repo_name: str, tag_name: str) -> None:
    """Print a repo where the tab hasn't been manipulated.

    Args:
        repo_name (str): The name of the repository
        tag_name (str): The name of the tag
    """
    print(f"{repo_name}: {GREEN}{tag_name} as expected{RESET}")


def print_no_tag(
    repo_name: str,
    tag_name: str,
) -> None:
    """Print a repo where we couldn't find the tag (based on the ref value).

    Args:
        repo_name (str): The name of the repository
        tag_name (str): The name of the reference associated with the tag
    """
    print(f"{repo_name}: {RED}{tag_name} not found{RESET}")
    print(
        " - Looks like the tag/reference has been deleted or has a "
        "different SHA"
    )
    print(" - Double-check it exists, and check the SHA in the repo with")


def print_no_matching_tag(
    repo_name: str,
    tag_name: str,
) -> None:
    """Print a repo where we couldn't find the tag (based on the ref value).

    Args:
        repo_name (str): The name of the repository
        tag_name (str): The name of the reference associated with the tag
    """
    print(f"{repo_name}: {RED}{tag_name} not found with matching SHA{RESET}")
    print(" - Check the SHA value after cloning the repo with:")
    print("       git show-ref --tags")


def print_no_object(
    repo_name: str,
    tag_name: str,
) -> None:
    """Print a repo where we couldn't find the object with a reference.

    Args:
        repo_name (str): The name of the repository
        tag_name (str): The name of the reference associated with the tag
    """
    print(f"{repo_name}: {RED}{tag_name}'s object not found{RESET}")
    print(" - Not associated with any commit")


def print_commit_sha_mismatch(
    repo_name: str, tag_name: str, commit_sha_exp: str, commit_sha_actual: str
) -> None:
    """Print a repo where the referenced commit SHAs don't match.

    Args:
        repo_name (str): The name of the repository
        tag_name (str): The name of the tag
        commit_sha_exp (str): The expected commit SHA
        commit_sha_actual (str): The actual commit SHA
    """
    if len(commit_sha_exp) > 6:
        commit_sha_exp = commit_sha_exp[:6] + "..."
    if len(commit_sha_actual) > 6:
        commit_sha_actual = commit_sha_actual[:6] + "..."
    print(f"{repo_name}: {RED}{tag_name} SHA mismatch{RESET}")
    print(f" - Commit's SHA: {commit_sha_actual} (expected {commit_sha_exp})")


def print_ref_sha_mismatch(
    repo_name: str, tag_name: str, ref_sha_exp: str, ref_sha_actual: str
) -> None:
    """Print a repo where the referenced commit SHAs don't match.

    Args:
        repo_name (str): The name of the repository
        tag_name (str): The name of the tag
        ref_sha_exp (str): The expected tag SHA
        ref_sha_actual (str): The actual tag SHA
    """
    if len(ref_sha_exp) > 6:
        ref_sha_exp = ref_sha_exp[:6] + "..."
    if len(ref_sha_actual) > 6:
        ref_sha_actual = ref_sha_actual[:6] + "..."
    print(f"{repo_name}: {RED}{tag_name} SHA mismatch{RESET}")
    print(f" - Tag's SHA: {ref_sha_actual} (expected {ref_sha_exp})")


# ------------------------------------------------------------------------
# Get the TagRecords
# ------------------------------------------------------------------------
# Only get the lab we need

# First, make sure that the spreadsheet and tab exist
try:
    sheet = _sheets.open_by_key(args.sheet_id)
except Exception:
    print(f"Issue accessing Google Sheet with ID '{args.sheet_id}'")
    print("Make sure it exists and is shared with your service account")
    sys.exit(1)

if args.tab not in [worksheet.title for worksheet in sheet.worksheets()]:
    print(f"Couldn't find tab '{args.tab}' in spreadsheet")
    sys.exit(1)


# Get the TagRecords, only needing the appropriate lab
class LabTagRecords(TagRecords):
    """Define our labs to keep track of."""

    labs = [args.lab]
    headers = get_tag_headers(labs)


spreadsheet_storer = SpreadsheetStorer[LabTagRecords](
    {"sheet_id": args.sheet_id, "tab": args.tab}
)

tag_records = spreadsheet_storer.get_records(logger=print, debug=False)

# Only need the ones with valid tags for the lab
tag_records = [
    record for record in tag_records if getattr(record, args.lab).tagged()
]

# ------------------------------------------------------------------------
# Iterate through, checking the repos
# ------------------------------------------------------------------------

num_tag_violations = 0

for record in tag_records:
    repo_name = record.repo_name
    issue_with_repo = False

    lab_tag = getattr(record, args.lab)
    tag_name = lab_tag.name
    ref_sha = lab_tag.ref_sha
    commit_sha = lab_tag.commit_sha

    # Check the actual values
    repo = _org.get_repo(repo_name)

    # Check the reference SHA
    tag_ref_name = f"refs/tags/{tag_name}"
    refs = repo.get_git_refs()
    tag_ref: Optional[github.GitRef.GitRef] = None
    for ref in refs:
        if ref.ref == tag_ref_name:
            tag_ref = ref
    if tag_ref is None:
        print_no_tag(repo_name, tag_name)
        issue_with_repo = True
    elif tag_ref.object is None:
        print_no_tag(repo_name, tag_name)
        issue_with_repo = True
    elif tag_ref.object.sha != ref_sha:
        print_ref_sha_mismatch(repo_name, tag_name, ref_sha, tag_ref.object.sha)
        issue_with_repo = True

    # Check the commit SHA
    if not issue_with_repo:
        git_tag = repo.get_git_tag(ref_sha)
        if git_tag.object is None:
            print_no_object(repo_name, tag_name)
            issue_with_repo = True
        elif git_tag.object.sha != commit_sha:
            issue_with_repo = True
            print_commit_sha_mismatch(
                repo_name, tag_name, commit_sha, git_tag.object.sha
            )

    if issue_with_repo:
        num_tag_violations += 1
    else:
        print_good_tag(repo_name, tag_name)

sys.exit(num_tag_violations)
