#!/usr/bin/env python
"""Upload the grades stored in a given Google Sheet.

Author: Aidan McNay
Date: October 28th, 2024
"""

import argparse
import canvasapi
import pydoc
import sys
from typing import Optional, TypedDict, Union

from canvas_steps import _course
from google_steps import _sheets

# ------------------------------------------------------------------------
# Arguments
# ------------------------------------------------------------------------

info_present = "-i" in sys.argv or "--info" in sys.argv

parser = argparse.ArgumentParser(
    description=("A script to upload grades from a Google Sheet to Canvas"),
)

parser.add_argument(
    "--sheet-id",
    help="The ID of the Google Sheet to get grades from",
    metavar="SHEET_ID",
    required=not info_present,
)
parser.add_argument(
    "--tab",
    help="The tab on the Google Sheet to get grades from",
    metavar="TAB",
    required=not info_present,
)
parser.add_argument(
    "--assignment",
    help="The assignment on Canvas to update",
    metavar="ASSIGNMENT",
    required=not info_present,
)
parser.add_argument(
    "-d",
    "--delete-comments",
    help="Delete pre-existing comments on the assignment",
    action="store_true",
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
parser.add_argument(
    "-s",
    "--silent",
    help="Don't print output",
    action="store_true",
)

# Parse the arguments
args = parser.parse_args()

# ------------------------------------------------------------------------
# Info
# ------------------------------------------------------------------------

info = f"""
{parser.format_usage()}

`upload-grades` is used to populate the grades for a Canvas assignment
based on a Google Sheet. Any information that was already part of the
Canvas assignment (including preexisting grades and/or comments) will be
deleted; the Google Sheet should be the ground truth for grades.

Arguments:
 - `sheet-id`: The ID of the Google Sheet to access (see the URL)
 - `tab`: The tab/worksheet of the Google Sheet to get the grades from
 - `assignment`: The assignment to populate on Canvas
 - `delete_comments`: Whether to delete pre-existing comments on
   assignment submissions

Assumptions:

`upload-grades` will iterate through the rows of the spreadsheet until
it finds one containing 'Grade'. It will assume that these are the
appropriate column headers, and will interpret all further rows as grade
submissions. Such headers can be hidden if desired for sheet aesthetics.

The following headers should be present:
 - 'Grade': The final grade for the assignment
 - 'NetID': The NetID of the student to be graded (individual assignment)
     OR the name of the group to be graded (group assignment)
 - 'Comment': (Optional) A comment to attach with the submission
 - <rubric-criterion-name>: For each criterion in the rubric attached to
     the assignment (if any), we expect a column with the exact criterion
     name, indicating the score for the criterion

Lastly, `upload-grades` assumes that the grading scheme for the assignment
on Canvas is either 'Points' or 'Letter Grade', and will cast values under
the 'Grade' column as appropriate. Further grading schemes can be supported
by modifying the 'cast_to_grade' function as appropriate.
"""

if args.info:
    pydoc.pager(info)
    exit(0)

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


def cast_to_grade(grade_val: str) -> Union[str, float]:
    """Cast a spreadsheet value to the appropriate type for a grade.

    Args:
        grade_val (str): The string from the spreadsheet

    Returns:
        Union[str, float]: The correct grade type for the assignment
    """
    if assignment is None:
        # Check again, otherwise linter will complain
        error(f"Couldn't find assignment '{args.assignment}'")
        sys.exit(1)

    grading_type = assignment.grading_type
    if grading_type == "points":
        return float(grade_val)
    elif grading_type == "letter_grade":
        return grade_val
    else:
        error(f"Unsupported grading type: '{grading_type}'")
        sys.exit(1)


# ------------------------------------------------------------------------
# Get the grade data from the spreadsheet, as a list of entries
# ------------------------------------------------------------------------
# {
#     "netid": "xxxx",
#     "grade": xxxx,
#     "rubric": {
#         "Criterion A": xxxx,
#         "Criterion B": xxxx,
#     }
# }
# (if it's a group assignment, "netid" represents the group name)


class StudentGrade(TypedDict):
    """A typed representation of a grade."""

    netid: str
    grade: Union[str, float]
    rubric: dict[str, float]
    comment: Optional[str]


def grade_from_row(
    row: list[str], headers: list[str], row_idx: int
) -> StudentGrade:
    """Create a grade from a spreadsheet row entry.

    Args:
        row (list[str]): The row to get data from
        headers (list[str]): The headers to index based on

    Returns:
        StudentGrade: The resulting grade object
    """

    def get_row_val(field: str) -> str:
        """Get a value from the row, indexing based on the headers.

        Args:
            row (list[str]): The row to get data from
            val (str): The field to get the data of

        Returns:
            str: The resulting data
        """
        return row[headers.index(field)]

    try:
        netid = get_row_val("NetID")
        grade = cast_to_grade(get_row_val("Grade"))
        rubric = {
            name: float(get_row_val(name))
            for name in criteria_id_name_mapping.values()
        }
    except Exception as e:
        error(
            f"Error converting grade data in row {row_idx} to a float: {str(e)}"
        )
        sys.exit(1)

    try:
        comment = get_row_val("Comment")
    except Exception:
        comment = None
    return {
        "netid": netid,
        "grade": grade,
        "rubric": rubric,
        "comment": comment,
    }


# Check that the spreadsheet is valid
try:
    sheet = _sheets.open_by_key(args.sheet_id)
except Exception:
    print(f"Issue accessing Google Sheet with ID '{args.sheet_id}'")
    print("Make sure it exists and is shared with your service account")
    sys.exit(1)

if args.tab not in [worksheet.title for worksheet in sheet.worksheets()]:
    print(f"Couldn't find tab '{args.tab}' in spreadsheet")
    sys.exit(1)

# Get the records from the spreadsheet
worksheet = sheet.worksheet(args.tab)
data = worksheet.get_all_values()

# Iterate to find headers
header_rank = 0
worksheet_headers = data[0]
while "Grade" not in worksheet_headers:
    if header_rank < len(data) - 1:
        header_rank += 1
        worksheet_headers = data[header_rank]
    else:
        error("Couldn't find header 'Grade' in worksheet; aborting...")
        sys.exit(1)

# Make sure we have all the required headers
if "NetID" not in worksheet_headers:
    error("Cound't find header 'NetID' in worksheet; aborting...")
    sys.exit(1)

for criteria_name in criteria_id_name_mapping.values():
    if criteria_name not in worksheet_headers:
        error(
            f"Cound't find header '{criteria_name}' in worksheet; aborting..."
        )
        sys.exit(1)

# Get the actual student data
grades: dict[str, StudentGrade] = {}

for idx, row in enumerate(data[(header_rank + 1) :]):
    grade = grade_from_row(row, worksheet_headers, header_rank + 1 + idx)
    grades[grade["netid"]] = grade

# ------------------------------------------------------------------------
# Upload the grades
# ------------------------------------------------------------------------

if is_group_assignment:
    submissions = assignment.get_submissions(
        include=["rubric_assessment", "group", "submission_comments"],
        grouped=True,
    )
else:
    submissions = assignment.get_submissions(
        include=["rubric_assessment", "user", "submission_comments"]
    )


def delete_comments(submission: canvasapi.submission.Submission) -> None:
    """Hacky way to delete existing comments.

    There exists an API endpoint for this (what we use), just not a
    Python wrapper (at time of writing).

    Args:
        submission (canvasapi.submission.Submission): The submission
        to delete the comments of
    """
    comments = submission.submission_comments
    requester = submission._requester

    # Metadata needed for endpoint
    course_id = submission.course_id
    assignment_id = submission.assignment_id
    user_id = submission.user_id
    partial_endpoint = (
        f"courses/{course_id}/assignments/{assignment_id}"
        f"/submissions/{user_id}/comments/"
    )

    for comment in comments:
        comment_id = comment["id"]
        endpoint = partial_endpoint + str(comment_id)
        requester.request("DELETE", endpoint)


for submission in submissions:
    if args.delete_comments:
        delete_comments(submission)
    netid = (
        submission.group["name"]
        if is_group_assignment
        else submission.user["login_id"]
    )
    if netid not in grades:
        if is_group_assignment and submission.group["name"] is not None:
            warning(f"No grade found for '{netid}'; skipping...")
        if (not is_group_assignment) and submission.user[
            "name"
        ] != "Test Student":
            warning(f"No grade found for '{netid}'; skipping...")
    else:
        if is_group_assignment:
            grade = grades[submission.group["name"]]
        else:
            grade = grades[netid]
        update_rubric = {
            rubric_id: {"points": grade["rubric"][rubric_value]}
            for rubric_id, rubric_value in criteria_id_name_mapping.items()
        }
        update_kwargs = {
            "submission": {"posted_grade": grade["grade"]},
            "rubric_assessment": update_rubric,
        }
        if grade["comment"]:
            update_kwargs["comment"] = {
                "text_comment": grade["comment"],
                "group_comment": True,
            }
        submission.edit(**update_kwargs)
        success(f"Updated grade for '{netid}'")
        del grades[netid]

success("All grades uploaded")

for netid in grades:
    warning(f"Grade given for '{netid}', but not found on Canvas")
