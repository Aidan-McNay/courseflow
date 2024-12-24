#!/usr/bin/env python
"""Pull the current grade status of an assignment to a Google Sheet.

Author: Aidan McNay
Date: October 3rd, 2024
"""

import argparse
import canvasapi
import sys
from typing import Optional, TypedDict
from utils.api_call import retry_call

from canvas_steps import _course
from google_steps import _sheets

# ------------------------------------------------------------------------
# Arguments
# ------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description=(
        "A script to populate a Google Sheet with assignment grades from "
        "Canvas"
    ),
)

parser.add_argument(
    "--sheet-id",
    help="The ID of the Google Sheet to populate",
    metavar="SHEET_ID",
    required=True,
)
parser.add_argument(
    "--tab",
    help="The tab on the Google Sheet to populate",
    metavar="TAB",
    required=True,
)
parser.add_argument(
    "--assignment",
    help="The assignment on Canvas to get",
    metavar="ASSIGNMENT",
    required=True,
)
parser.add_argument(
    "-n",
    "--no-color",
    help="Don't print in color (use for file logging)",
    action="store_true",
)
parser.add_argument(
    "-s",
    "--silent",
    help="Don't print output",
    action="store_true",
)

# Parse the arguments
args = parser.parse_args()

# ------------------------------------------------------------------------
# Printing functions
# ------------------------------------------------------------------------

if args.no_color:
    RED = ""
    YELLOW = ""
    GREEN = ""
    END = ""
else:
    RED = "\033[1;31m"
    YELLOW = "\033[1;33m"
    GREEN = "\033[1;32m"
    END = "\033[0m"


def warning(msg: str) -> None:
    """Print a warning."""
    if not args.silent:
        print(f"{YELLOW}{msg}{END}")


def success(msg: str) -> None:
    """Print a success indicator."""
    if not args.silent:
        print(f"{GREEN}{msg}{END}")


def error(msg: str) -> None:
    """Print an error."""
    if not args.silent:
        print(f"{RED}{msg}{END}")


# ------------------------------------------------------------------------
# Get the assignment, as well as all of the rubric criteria
# ------------------------------------------------------------------------

assignment: Optional[canvasapi.assignment.Assignment] = None

for curr_assignment in _course.get_assignments():
    if curr_assignment.name == args.assignment:
        assignment = curr_assignment

if assignment is None:
    error(f"Couldn't find assignment '{args.assignment}'")
    sys.exit(1)
else:
    success(f"Found assignment '{args.assignment}'")

is_group_assignment = assignment.group_category_id is not None

criteria_id_name_mapping = {}

if hasattr(assignment, "rubric"):
    for criterion in assignment.rubric:
        criteria_id_name_mapping[criterion["id"]] = criterion["description"]

# ------------------------------------------------------------------------
# Get the submissions as a dictionary with specific attributes
# ------------------------------------------------------------------------
# {
#     "netid": "xxxx",
#     "rubric": {
#         "Criterion A": {
#             "graded": True,
#             "gave_comment": True,
#             "points": 5.25
#         },
#         "Criterion B": {
#             "graded": True
#             "gave_comment": False,
#             "points": 4.00
#         }
#     }
# }


class Criterion(TypedDict):
    """A typed representation of a criterion."""

    graded: bool
    gave_comment: bool
    points: Optional[float]


class StudentSubmission(TypedDict):
    """A typed representation of a submission."""

    first_name: str
    last_name: str
    netid: str
    rubric: dict[str, Criterion]


student_submissions: list[StudentSubmission] = []

submissions = assignment.get_submissions(include=["rubric_assessment", "user"])
for submission in submissions:
    if submission.user["name"] == "Test Student":
        continue
    netid = submission.user["login_id"]
    name_components = submission.user["sortable_name"].split(",")
    last_name = name_components[0].strip()
    first_name = name_components[1].strip()

    rubric: dict[str, Criterion] = {}
    if hasattr(submission, "rubric_assessment"):
        for criterion_id, criterion_name in criteria_id_name_mapping.items():
            if criterion_id in submission.rubric_assessment:
                rating = submission.rubric_assessment[criterion_id]
                if "points" in rating:
                    points = rating["points"]
                else:
                    points = None
                gave_comment = "comments" in rating and rating["comments"] != ""
                rubric[criterion_name] = {
                    "graded": True,
                    "gave_comment": gave_comment,
                    "points": points,
                }
            else:
                rubric[criterion_name] = {
                    "graded": False,
                    "gave_comment": False,
                    "points": None,
                }
    else:
        for criterion_name in criteria_id_name_mapping.values():
            rubric[criterion_name] = {
                "graded": False,
                "gave_comment": False,
                "points": 0,
            }
    student_submissions.append(
        {
            "first_name": first_name,
            "last_name": last_name,
            "netid": netid,
            "rubric": rubric,
        }
    )

success(f"Found {len(student_submissions)} submissions")

student_submissions.sort(key=lambda x: x["netid"])

# ------------------------------------------------------------------------
# Get the relevant worksheet
# ------------------------------------------------------------------------

try:
    sheet = retry_call(_sheets.open_by_key, args.sheet_id)
except Exception:
    error(f"Couldn't access spreadsheet with ID '{args.sheet_id}'")
    error("Make sure it exists and is shared with the service account")

if args.tab in [worksheet.title for worksheet in sheet.worksheets()]:
    worksheet = retry_call(sheet.worksheet, args.tab)
else:
    warning(f"Creating new tab '{args.tab}'")
    worksheet = retry_call(sheet.add_worksheet, title=args.tab, rows=1, cols=1)

# ------------------------------------------------------------------------
# Write the submissions to the worksheet
# ------------------------------------------------------------------------

criteria_names = [name for name in criteria_id_name_mapping.values()]

criteria_headers: list[str] = []
criteria_subheaders: list[str] = []

for name in criteria_names:
    criteria_headers.append(name)
    criteria_headers.append("")
    criteria_headers.append("")
    criteria_subheaders.append("Graded?")
    criteria_subheaders.append("Points")
    criteria_subheaders.append("Comment?")

headers = ["First Name", "Last Name", "Netid"] + criteria_headers
subheaders = ([""] * 3) + criteria_subheaders
cells = [headers, subheaders]

for student_submission in student_submissions:
    entry = [
        student_submission["first_name"],
        student_submission["last_name"],
        student_submission["netid"],
    ]
    for criterion_name in criteria_names:
        criterion = student_submission["rubric"][criterion_name]
        entry.append("Y" if criterion["graded"] else "N")
        entry.append(
            "N/A" if criterion["points"] is None else criterion["points"]
        )
        entry.append("Y" if criterion["gave_comment"] else "N")
    cells.append(entry)

retry_call(worksheet.clear)
retry_call(worksheet.update, cells)

# ------------------------------------------------------------------------
# Merge headers
# ------------------------------------------------------------------------


def get_col(column_int: int) -> str:
    """Get the column for a given column number.

    https://stackoverflow.com/a/23862195/23068975
    """
    start_index = 1
    letter = ""
    while column_int > 25 + start_index:
        letter += chr(65 + int((column_int - start_index) / 26) - 1)
        column_int = column_int - (int((column_int - start_index) / 26)) * 26
    letter += chr(65 - start_index + (int(column_int)))
    return letter


num_cols_to_merge = len(criteria_headers) / 3
col_to_merge = 4
while num_cols_to_merge > 0:
    col_start = get_col(col_to_merge)
    col_end = get_col(col_to_merge + 2)
    retry_call(worksheet.merge_cells, f"{col_start}1:{col_end}1")
    col_to_merge += 3
    num_cols_to_merge -= 1

success("Updated the spreadsheet")
