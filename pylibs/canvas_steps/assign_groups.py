"""Assign groups to a group category on Canvas.

Author: Aidan McNay
Date: September 16th, 2024
"""

import canvasapi
from datetime import datetime
import random
import re
from threading import Lock
from typing import Any, Callable, cast, Optional, Self

from canvas_steps import _canvas, _course
from flow.admin_step import AdminPropagateStep
from records.student_record import StudentRecord

random.seed(0xDEADBEEF)

# ------------------------------------------------------------------------
# AssignGroups
# ------------------------------------------------------------------------


class AssignGroups(AdminPropagateStep[StudentRecord]):
    """A propagate step to assign students to a group on Canvas."""

    description = "Assign remaining students to a group on Canvas randomly."

    config_types = [
        ("group_category", str, "The category to fill in on Canvas"),
        (
            "canvas_group_regex",
            str,
            (
                "The regex to extract group numbers from Canvas group names. "
                "The number will be the first matching group in the regex "
                r"(ex. 'ECE 2300: Lab Group (\d+)'). "
                "Use single quotes to specify"
            ),
        ),
        ("form_date", datetime, "When we should form and log groups"),
        (
            "canvas_group_pattern",
            str,
            (
                "The format to make new Canvas groups with. <num> will be "
                "replaced with the group number. Should be complementary with "
                "canvas_group_regex"
            ),
        ),
    ]

    def get_group_num(self: Self, name: str) -> int:
        """Get the number from a Canvas group.

        Args:
            self (Self): The relevant propagate step
            name (str): The name of the group

        Returns:
            int: The number for the Canvas group
        """
        pattern = re.compile(r"{}".format(self.configs.canvas_group_regex))
        match = pattern.fullmatch(name)
        if match:
            return int(match.group(1))
        else:
            raise Exception(f"Couldn't get number from group name: {name}")

    def get_group_name(self: Self, num: int) -> str:
        """Get the appropriate Canvas group name for the corresponding number.

        Args:
            self (Self): The relevant propagate step
            num (int): The group number

        Returns:
            str: The group name
        """
        return cast(
            str, self.configs.canvas_group_pattern.replace("<num>", str(num))
        )

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        # Check that the category exists
        curr_category: Optional[canvasapi.group.GroupCategory] = None
        categories = _course.get_group_categories()

        for category in categories:
            if category.name == self.configs.group_category:
                curr_category = category

        if curr_category is None:
            raise Exception(
                f"No group category '{self.configs.group_category}' on Canvas"
            )

        # Check that our regex pattern works
        test_group_name = self.get_group_name(69)
        group_num = self.get_group_num(test_group_name)
        if group_num != 69:
            raise Exception(
                "Couldn't extract group number with regex "
                f"({self.configs.canvas_group_regex}) after "
                "formatting with group pattern "
                f"({self.configs.canvas_group_pattern})"
            )

        # Check that we can extract unique ints from our group names
        nums_found: set[int] = set()

        groups = curr_category.get_groups()
        for group in groups:
            try:
                group_num = self.get_group_num(group.name)
            except Exception:
                raise Exception(
                    f"Couldn't match '{self.configs.canvas_group_regex}' "
                    f"with {group.name}"
                )
            if group_num in nums_found:
                raise Exception(f"Multiple groups for number {str(group_num)}")
            nums_found.add(group_num)

    def signed_up_users(
        self: Self, category: canvasapi.group.GroupCategory
    ) -> list[canvasapi.user.User]:
        """Get the users who've signed up for the group.

        Args:
            self (Self): The relevant propagate step
            category (canvasapi.group.GroupCategory): The category to look at

        Returns:
            list[str]: The signed-up users.
        """
        users = []

        groups = category.get_groups()
        for group in groups:
            students = group.get_users()
            for student in students:
                users.append(student)

        return users

    def get_section_mapping(self: Self) -> dict[str, canvasapi.user.User]:
        """Get a mapping of sections to the students in the section.

        Args:
            self (Self): The relevant propagate step

        Returns:
            dict[str, list[str]]: The mapping of sections to lists of students
        """
        lab_sections = [
            section
            for section in _course.get_sections()
            if "LAB" in section.name
        ]

        section_students_mapping = {}

        for section in lab_sections:
            name = section.name
            student_objs = _canvas.get_section(
                section, include=["students"]
            ).students
            students = [_course.get_user(obj["id"]) for obj in student_objs]
            random.shuffle(students)
            section_students_mapping[name] = students

        return section_students_mapping

    def get_section(self: Self, user: canvasapi.user.User) -> str:
        """Get the name of the lab section that a student is in.

        Args:
            self (Self): The relevant propagate step
            user (canvasapi.user.User): The user

        Returns:
            str: The lab section of the user
        """
        lab_sections = [
            section
            for section in _course.get_sections()
            if "LAB" in section.name
        ]

        for section in lab_sections:
            student_objs = _canvas.get_section(
                section, include=["students"]
            ).students
            students = [_course.get_user(obj["id"]) for obj in student_objs]
            for student in students:
                if student == user:
                    return cast(str, section.name)

        raise Exception(f"Couldn't find {user.login_id}'s section!")

    def should_pair(self: Self) -> bool:
        """Determine whether we should pair students into groups.

        Args:
            self (Self): The relevant propagate step

        Returns:
            bool: Whether we should be pairing
        """
        # Don't ping before the scheduled date
        now = datetime.now()
        if now < self.configs.form_date:
            return False
        return True

    def propagate_records(
        self: Self,
        records: list[tuple[StudentRecord, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Create the groups, updating the records and Canvas.

        We additionally set the metadata 'old_groups' to a dictionary mapping
        NetIDs to their previous group numbers (dict[str, int])

        Args:
            records (list[RecordType]): The list of records to manipulate
            logger (Callable[[str], None]): A function to log any notable
              events
            get_metadata (Callable[[str], Any],): A function to retrieve global
              metadata previously set in the flow
            debug (bool, optional): Whether we are in "debug" mode. In debug
              mode, no external state should be modified, and we are free to
              inject dummy information. Defaults to False.
        """
        if not self.should_pair():
            return

        # The overall mapping from group names to numbers and students, as well
        # as whether we need to update Canvas
        group_mapping: dict[
            str, tuple[int, list[canvasapi.user.User], bool]
        ] = {}

        # Get the relevant category
        curr_category: Optional[canvasapi.group.GroupCategory] = None
        categories = _course.get_group_categories()

        for category in categories:
            if category.name == self.configs.group_category:
                curr_category = category

        if curr_category is None:
            raise Exception(
                f"No group category '{self.configs.group_category}' on Canvas"
            )

        # Turn off self-signup
        if debug:
            logger("DEBUG: Avoiding disabling self-signup")
        else:
            curr_category.update(self_signup=None)
            logger(f"Disabling self-signup for {curr_category.name}")

        # Remove any solo students
        # groups = curr_category.get_groups()
        # for group in groups:
        #     students = list(group.get_users())
        #     if len(students) < 2:
        #         for student in students:
        #             if debug:
        #                 logger(
        #                     "DEBUG: Not removing solo student "
        #                     f"{student.login_id} from {group.name}"
        #                 )
        #             else:
        #                 group.remove_user(student)
        #                 logger(
        #                     "Removed solo student "
        #                     f"{student.login_id} from {group.name}"
        #                 )

        # Get section mapping
        section_students_mapping = self.get_section_mapping()

        # Don't match students already in a group
        nums_already_used: set[int] = set()
        students_already_paired: list[str] = []

        groups = curr_category.get_groups()
        for group in groups:
            students = list(group.get_users())
            if len(students) > 1:
                name = group.name
                num = self.get_group_num(name)
                group_mapping[name] = (num, students, False)

                nums_already_used.add(num)
                for student in students:
                    students_already_paired.append(student.login_id)

        remaining_section_students_mapping = {
            sec: [
                student
                for student in students
                if student.login_id not in students_already_paired
            ]
            for sec, students in section_students_mapping.items()
        }

        # Match remaining students
        def get_next_num() -> int:
            """Get the next number to use for a group."""
            num_to_use = 1
            while num_to_use in nums_already_used:
                num_to_use += 1
            nums_already_used.add(num_to_use)
            return num_to_use

        for section, students in remaining_section_students_mapping.items():
            if len(students) > 1:  # Easy case - pair as normal
                while len(students) > 3:
                    group_students = students[:2]
                    group_num = get_next_num()
                    group_name = self.get_group_name(group_num)
                    group_mapping[group_name] = (
                        group_num,
                        group_students,
                        True,
                    )
                    students = students[2:]

                # Match remaining people
                if len(students) > 0:
                    group_num = get_next_num()
                    group_name = self.get_group_name(group_num)
                    group_mapping[group_name] = (
                        group_num,
                        students,
                        True,
                    )
                    students = []

            elif len(students) > 0:  # Hard case - one student
                # Stick with a pre-existing group
                put_in_group = False

                for group_name, group in group_mapping.items():
                    same_section = False
                    for student in group[1]:
                        if self.get_section(student) == section:
                            same_section = True
                            break
                    if same_section:
                        group_mapping[group_name] = (
                            group[0],
                            group[1] + students,
                            True,
                        )
                        put_in_group = True
                        logger(
                            f"Putting {student[0].login_id} in pre-existing "
                            f"group {group_name}"
                        )
                        break
                if not put_in_group:  # Very unlikely
                    raise Exception(
                        f"Failed to put {students[0].login_id} in a group"
                    )
                students = []

            else:  # No students
                continue

        # Update Canvas as appropriate
        for group_name, (
            group_num,
            students,
            update_canvas,
        ) in group_mapping.items():
            if update_canvas:
                student_netids = ", ".join(
                    [student.login_id for student in students]
                )
                if debug:
                    logger(
                        f"DEBUG: Avoiding updating Canvas with {group_name} "
                        f"having {student_netids}"
                    )
                else:
                    # Delete group
                    for group in groups:
                        if group.name == group_name:
                            group.delete()

                    # Create the group
                    new_group = curr_category.create_group(name=group_name)

                    # Add the students
                    for student in students:
                        new_group.create_membership(student)

        # Map NetIDs to group numbers
        netid_num_mapping: dict[str, int] = {}
        for _, (num, students, _) in group_mapping.items():
            for student in students:
                netid_num_mapping[student.login_id] = num

        # Update our records
        old_groups: dict[str, int] = {}
        for record, lock in records:
            with lock:
                if record.enrolled:
                    if record.netid in netid_num_mapping:
                        num = netid_num_mapping[record.netid]
                        if debug:
                            logger(
                                f"DEBUG: Avoid logging {record.netid} in "
                                f"Group {str(num)}"
                            )
                        else:
                            if record.group_num:
                                if record.group_num != num:
                                    old_groups[record.netid] = record.group_num
                                    record.group_num = num
                                    logger(
                                        f"Reassigned {record.netid} to Group "
                                        f"{num}"
                                    )
                            else:
                                record.group_num = num
                                logger(
                                    f"Assigned {record.netid} to Group {num}"
                                )
        set_metadata("old_groups", old_groups)
