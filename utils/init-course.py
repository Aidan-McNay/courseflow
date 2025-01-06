#!/usr/bin/env python
"""Initialize a course with the given content.

Author: Aidan McNay
Date: December 29th, 2024
"""

import argparse
import canvasapi
from dataclasses import dataclass, field
import datetime
import pydoc
import sys
from typing import Optional, Self, Union
import yaml

from canvas_steps import _course

# ------------------------------------------------------------------------
# Arguments
# ------------------------------------------------------------------------

info_present = "-i" in sys.argv or "--info" in sys.argv

parser = argparse.ArgumentParser(
    description=("A script to initialize a Canvas course"),
)

parser.add_argument(
    "-a",
    "--attributes",
    help="The attributes to initialize the course with",
    metavar="YAML_FILE",
    required=not info_present,
)
parser.add_argument(
    "-r",
    "--reset",
    help=(
        "Reset the Canvas course, deleting all previously-created attributes"
    ),
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

`init-course` is used to initialize a Canvas course with various
components, including assignments, quizzes, and student groups. This
allows instructors to expedite the setup of recurring offerings, as well
as to configure the course in a text-based, reproducible format.

Arguments:
 - `attributes`: The YAML file specifying components of the course
 - `reset`: Whether to reset the course in its entirety

`init-course` takes in a YAML file with specifications of the various
course components to initialize the course from. See the documentation
and the example attribute file for examples.

Note that additional configurations may be necessary (such as the
creation of rubrics and their mapping to assignments). This is not
included, due to the difficulty of representation in a YAML file;
instead, other utilities should be used for their creation.

In addition, `init-course` allows a user to reset the course,
specifically any previously-made attributes (assignments, assignment
groups, group categories, and quizzes). This can be used to wipe any
pre-existing content (in order to start from a blank slate). Resetting
the course, along with providing an initialization file, will result in
a course with the same attributes. However, wiped content cannot be
(easily) retrieved, and should therefore be used cautiously.
`init-course` will prompt for confirmation whenever using this feature,
even if run silently.
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


def warning(msg: str, always_print: bool = True) -> None:
    """Print a warning."""
    if (not args.silent) or always_print:
        print(f"{YELLOW}{msg}{END}")


def success(msg: str) -> None:
    """Print a success indicator."""
    if not args.silent:
        print(f"{GREEN}{msg}{END}")


def error(msg: str) -> None:
    """Print an error."""
    print(f"{RED}{msg}{END}")


# ------------------------------------------------------------------------
# Parse the course attributes file
# ------------------------------------------------------------------------


@dataclass
class Assignment:
    """Representation of an assignment attribute."""

    name: str
    description: str = ""
    assignment_group: Optional[str] = None
    submission_types: list[str] = field(default_factory=lambda: ["none"])
    allowed_extensions: list[str] = field(default_factory=lambda: ["pdf"])
    grading_type: str = "points"
    points_possible: float = 5.25
    group_category: Optional[str] = None
    published: bool = False
    due_at: Optional[datetime.datetime] = None
    lock_at: Optional[datetime.datetime] = None
    unlock_at: Optional[datetime.datetime] = None

    def create(self: Self, course: canvasapi.course.Course) -> None:
        """Create the assignment in the given course.

        Args:
            course (canvasapi.course.Course): The course to create the
              assignment in
        """
        assignment_args = {
            "name": self.name,
            "description": "<p>"
            + self.description.strip(" \n")
            .replace("\n\n", "<br><br>")
            .replace("\n", "")
            + "</p>",
            "submission_types": self.submission_types,
            "grading_type": self.grading_type,
            "published": self.published,
        }

        if "online_upload" in self.submission_types:
            assignment_args["allowed_extensions"] = self.allowed_extensions
        if self.grading_type == "points":
            assignment_args["points_possible"] = self.points_possible
        if self.due_at:
            assignment_args["due_at"] = self.due_at
        if self.lock_at:
            assignment_args["lock_at"] = self.lock_at
        if self.unlock_at:
            assignment_args["unlock_at"] = self.unlock_at

        if self.assignment_group:
            found_group = False
            for group in course.get_assignment_groups():
                if group.name == self.assignment_group:
                    found_group = True
                    assignment_args["assignment_group_id"] = group.id
                    break
            if not found_group:
                error(
                    f"Couldn't add assignment '{self.name}' to assignment "
                    f"group {self.assignment_group}; no such assignment "
                    "group exists..."
                )
                sys.exit(1)

        if self.group_category:
            found_group = False
            for group in course.get_group_categories():
                if group.name == self.group_category:
                    found_group = True
                    assignment_args["group_category_id"] = group.id
                    break
            if not found_group:
                error(
                    f"Couldn't add assignment '{self.name}' to group category "
                    f"{self.group_category}; no such group category exists..."
                )
                sys.exit(1)

        for assignment in course.get_assignments():
            if assignment.name == self.name:
                warning(
                    f"An assignment named '{self.name}' already "
                    "exists; continuing..."
                )
                return

        course.create_assignment(assignment=assignment_args)
        success(f"Created assignment '{self.name}'")


@dataclass
class AssignmentGroup:
    """Representation of an assignment group."""

    name: str
    weight: Optional[int] = None

    def create(self: Self, course: canvasapi.course.Course) -> None:
        """Create the assignment group in the given course.

        Args:
            course (canvasapi.course.Course): The course to create the
              assignment group in
        """
        assignment_group_args: dict[str, Union[str, int]] = {"name": self.name}
        if self.weight:
            assignment_group_args["group_weight"] = self.weight

        for assignment_group in course.get_assignment_groups():
            if assignment_group.name == self.name:
                warning(
                    f"An assignment group named '{self.name}' already "
                    "exists; continuing..."
                )
                return

        course.create_assignment_group(**assignment_group_args)
        success(f"Created assignment group '{self.name}'")


@dataclass
class GroupCategory:
    """Representation of a group category."""

    name: str
    self_signup: Optional[str] = None

    def create(self: Self, course: canvasapi.course.Course) -> None:
        """Create the group category in the given course.

        Args:
            course (canvasapi.course.Course): The course to create the
              group category in
        """
        group_category_args = {"name": self.name}
        if self.self_signup:
            group_category_args["self_signup"] = self.self_signup

        for category in course.get_group_categories():
            if category.name == self.name:
                warning(
                    f"A group category named '{self.name}' already "
                    "exists; continuing..."
                )
                return

        course.create_group_category(**group_category_args)
        success(f"Created group category '{self.name}'")


@dataclass
class QuizQuestion:
    """Representation of a question for a quiz."""

    name: str
    text: str
    type: str = "short_answer_question"
    points_possible: int = 0

    def add(self: Self, quiz: canvasapi.quiz.Quiz) -> None:
        """Add the question to the given quiz.

        Args:
            quiz (canvasapi.quiz.Quiz): The quiz to add the
              question to
        """
        question_args = {
            "question_name": self.name,
            "question_text": self.text,
            "question_type": self.type,
            "points_possible": self.points_possible,
        }
        quiz.create_question(question=question_args)


@dataclass
class Quiz:
    """Representation of a quiz."""

    title: str
    description: str = ""
    quiz_type: str = "survey"
    assignment_group: Optional[str] = None
    published: bool = False
    due_at: Optional[datetime.datetime] = None
    lock_at: Optional[datetime.datetime] = None
    unlock_at: Optional[datetime.datetime] = None
    questions: list[QuizQuestion] = field(default_factory=list)
    allowed_attempts: Optional[int] = None

    def create(self: Self, course: canvasapi.course.Course) -> None:
        """Create the quiz in the given course.

        Args:
            course (canvasapi.course.Course): The course to create the
              quiz in
        """
        quiz_args = {
            "title": self.title,
            "description": "<p>"
            + self.description.strip(" \n")
            .replace("\n\n", "<br><br>")
            .replace("\n", "")
            + "</p>",
            "quiz_type": self.quiz_type,
            "published": False,
        }
        if self.due_at:
            quiz_args["due_at"] = self.due_at
        if self.lock_at:
            quiz_args["lock_at"] = self.lock_at
        if self.unlock_at:
            quiz_args["unlock_at"] = self.unlock_at
        if self.allowed_attempts:
            quiz_args["allowed_attempts"] = self.allowed_attempts

        if (
            self.quiz_type in ("assignment", "graded_survey")
            and self.assignment_group
        ):
            found_group = False
            for group in course.get_assignment_groups():
                if group.name == self.assignment_group:
                    found_group = True
                    quiz_args["assignment_group_id"] = group.id
                    break
            if not found_group:
                error(
                    f"Couldn't add assignment '{self.title}' to assignment "
                    f"group {self.assignment_group}; no such assignment "
                    "group exists..."
                )
                sys.exit(1)

        for quiz in course.get_quizzes():
            if quiz.title == self.title:
                warning(
                    f"A quiz named '{self.title}' already "
                    "exists; continuing..."
                )
                return

        new_quiz = course.create_quiz(quiz=quiz_args)
        for question in self.questions:
            question.add(new_quiz)
        if self.published:
            new_quiz.edit(quiz={"published": True, "notify_of_update": False})
        success(f"Created quiz '{self.title}'")


with open(args.attributes, "r") as f:
    configs = yaml.safe_load(f)

assignments: list[Assignment] = []
assignment_groups: list[AssignmentGroup] = []
group_categories: list[GroupCategory] = []
quizzes: list[Quiz] = []

if "assignments" in configs:
    for assignment in configs["assignments"]:
        assignments.append(Assignment(**assignment))

if "assignment_groups" in configs:
    for assignment_group in configs["assignment_groups"]:
        assignment_groups.append(AssignmentGroup(**assignment_group))

if "group_categories" in configs:
    for category in configs["group_categories"]:
        group_categories.append(GroupCategory(**category))

if "quizzes" in configs:
    for quiz in configs["quizzes"]:
        questions: list[QuizQuestion] = []
        if "questions" in quiz:
            for question in quiz["questions"]:
                questions.append(QuizQuestion(**question))
        quiz["questions"] = questions
        quizzes.append(Quiz(**quiz))

# ------------------------------------------------------------------------
# Update the course
# ------------------------------------------------------------------------


def reset_course(_course: canvasapi.course.Course) -> None:
    """Delete any pre-existing attributes from the course.

    Args:
        _course (canvasapi.course.Course): The course to delete content
          from
    """
    # Delete assignments
    for assignment in _course.get_assignments():
        assignment.delete()

    # Delete quizzes
    for quiz in _course.get_quizzes():
        quiz.delete()

    # Delete assignment groups
    for assignment_group in _course.get_assignment_groups():
        assignment_group.delete()

    # Delete group categories
    for group_category in _course.get_group_categories():
        group_category.delete()


if args.reset:
    confirm_msg = f"I want to erase {_course.name}"
    warning(
        always_print=True,
        msg="WARNING: You are about to erase all previous "
        f"attributes from the course '{_course.name}'. Are "
        "you sure to wish to proceed?\n\n"
        f"To confirm, type '{confirm_msg}':",
    )
    while input("") != confirm_msg:
        warning("Incorrect confirmation message", always_print=True)
    reset_course(_course)

for assignment_group in assignment_groups:
    assignment_group.create(_course)

for group_category in group_categories:
    group_category.create(_course)

for assignment in assignments:
    assignment.create(_course)

for quiz in quizzes:
    quiz.create(_course)
