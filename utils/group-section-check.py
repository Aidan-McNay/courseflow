#!/usr/bin/env python
"""Check section homogeneity for groups in a group category.

The script will analyze the lab sections of students in each group, and
display either the common section, or a detailing of the mismatched sections.

The return code is the number of mismatching groups.

Author: Aidan McNay
Date: September 21st, 2024
"""

import argparse
import canvasapi
import pydoc
import sys
from typing import Optional

from canvas_steps import _canvas, _course

# ------------------------------------------------------------------------
# Arguments
# ------------------------------------------------------------------------

info_present = "-i" in sys.argv or "--info" in sys.argv

parser = argparse.ArgumentParser(
    description=(
        "A simple script to check students in groups are in the "
        "same lab section"
    ),
)

parser.add_argument(
    "-c",
    "--category",
    help="The Canvas group category/set to check",
    metavar="GROUP_SET",
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

`group-section-check` is used to ensure that, for a given group category,
all groups consist only of students in the same lab section. This is to
ensure that students haven't accidentally signed up to be in a lab group
with someone from a different lab (and can also be used to verify
lab groupings).

Arguments:
 - `category`: The group category to check on Canvas

Assumptions:

`group-section-check` uses the Canvas sections to check for section
homogeneity, and assumes that a section corresponds to a lab section if
and only if the section name contains 'LAB' (as is the case at time of
writing for sections populated by Cornell). If this ever becomes not the
case, please modify the assignment to `lab_sections`. Future versions of
the script might take in a regex to identify lab sections, if needed.
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


def print_same_section(group_name: str, section: str) -> None:
    """Print a group name where the members are in the same section.

    Args:
        group_name (str): The name of the group
        section (str): The common section
    """
    print(f"{group_name}: {GREEN}{section}{RESET}")


def print_multiple_sections(
    group_name: str, sections: list[tuple[str, str]]
) -> None:
    """Print a group name where the members are in different sections.

    Args:
        group_name (str): The name of the group
        sections (list[tuple[str, str]]): A list of (netid, section) pairings
    """
    print(f"{group_name}: {RED}Multiple Sections:{RESET}")
    for netid, section in sections:
        print(f" - {netid}: {section}")


# ------------------------------------------------------------------------
# Get the relevant category
# ------------------------------------------------------------------------

categories = _course.get_group_categories()

category: Optional[canvasapi.group.GroupCategory] = None
for curr_category in categories:
    if curr_category.name == args.category:
        category = curr_category

if category is None:
    print(f"No group category named '{args.category}' found!")
    sys.exit(1)

# ------------------------------------------------------------------------
# Get students by lab section
# ------------------------------------------------------------------------

lab_sections = [
    section for section in _course.get_sections() if "LAB" in section.name
]

# {
#     "netid1": "lab_section_3",
#     "netid2": "lab_section_1",
#     ...
# }
students_in_sections = {}

for section in lab_sections:
    name = section.name
    student_objs = _canvas.get_section(section, include=["students"]).students
    students = [_course.get_user(obj["id"]) for obj in student_objs]
    for student in students:
        students_in_sections[student.login_id] = name

# ------------------------------------------------------------------------
# Get groups
# ------------------------------------------------------------------------

num_mismatch_groups = 0

groups = category.get_groups()
for group in groups:
    students = list(group.get_users())
    if len(students) > 0:
        # Check section homogeneity
        section = students_in_sections[students[0].login_id]
        homogenous = all(
            [
                students_in_sections[student.login_id] == section
                for student in students
            ]
        )
        if homogenous:
            print_same_section(group.name, section)
        else:
            print_multiple_sections(
                group.name,
                [
                    (student.login_id, students_in_sections[student.login_id])
                    for student in students
                ],
            )
            num_mismatch_groups += 1

sys.exit(num_mismatch_groups)
