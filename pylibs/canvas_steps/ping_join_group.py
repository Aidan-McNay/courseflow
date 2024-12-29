"""Ping users who haven't yet joined a group on Canvas.

Author: Aidan McNay
Date: September 19th, 2024
"""

import canvasapi
from datetime import datetime
import os
from threading import Lock
from typing import Any, Callable, Optional, Self

from canvas_steps import _course
from flow.flow_steps import FlowPropagateStep
from records.student_record import StudentRecord
from utils.mailer import Mailer

# -----------------------------------------------------------------------------
# PingJoinGroup
# -----------------------------------------------------------------------------


class PingJoinGroup(FlowPropagateStep[StudentRecord]):
    """Ping users who haven't joined a group on Canvas."""

    description = "Email students who haven't joined a Canvas group"

    config_types = [
        ("start_date", datetime, "When to start emailing students"),
        ("email_gap", int, "The number of days between reminder emails"),
        (
            "email_template",
            str,
            (
                "The path to the template email (text file) to send. "
                "Instances of <first_name> and <last_name> will "
                "be replaced appropriately"
            ),
        ),
        (
            "send_email",
            str,
            "The email to send from (matching `GMAIL_API_KEY`)",
        ),
        ("subject", str, "The subject that the email should be sent with"),
        ("group_category", str, "The category to check on Canvas"),
    ]

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        if self.configs.email_gap <= 0:
            raise Exception("Please choose a positive email gap!")
        if not os.path.isfile(self.configs.email_template):
            raise Exception(f"Path {self.configs.email_template} isn't a file!")

        # Make sure that we can access the email
        try:
            Mailer(self.configs.send_email)
        except Exception:
            raise Exception(
                f"Couldn't log into '{self.configs.send_email}'"
                " - double-check your API key"
            )

        # Check that the category exists
        found_category = False
        categories = _course.get_group_categories()

        for category in categories:
            if category.name == self.configs.group_category:
                found_category = True

        if not found_category:
            raise Exception(
                f"No group category '{self.configs.group_category}' on Canvas"
            )

    def should_ping(self: Self, record: StudentRecord) -> bool:
        """Determine whether to ping a student, based on their record.

        Args:
            self (Self): The relevant propagate step
            record (StudentRecord): The record to potentially ping

        Returns:
            bool: Whether to ping the student
        """
        # Don't ping before the scheduled date
        now = datetime.now()
        if now < self.configs.start_date:
            return False

        # If we've pinged before, don't ping again within the gap
        if record.last_group_ping:
            # Always round to the hour the ping happened in, to avoid random
            # drift over time
            last_ping = record.last_group_ping.replace(
                minute=0, second=0, microsecond=0
            )
            if (now - last_ping).days < self.configs.email_gap:
                return False

        return True

    def signed_up_users(self: Self) -> list[str]:
        """Get the users who've signed up for the group.

        Args:
            self (Self): The relevant propagate step

        Returns:
            list[str]: The NetIDs of signed-up users.
        """
        netids = []

        categories = _course.get_group_categories()

        curr_category: Optional[canvasapi.group.GroupCategory] = None
        for category in categories:
            if category.name == self.configs.group_category:
                curr_category = category

        if curr_category is None:
            raise Exception("Category not found (after validation?)")

        groups = curr_category.get_groups()
        for group in groups:
            students = group.get_users()
            for student in students:
                netids.append(student.login_id)

        return netids

    def propagate_records(
        self: Self,
        records: list[tuple[StudentRecord, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Email students who haven't submitted a username.

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
        with open(self.configs.email_template, "r") as f:
            email_template = f.read()
        signed_up_users = self.signed_up_users()

        for record, lock in records:
            with lock:
                if (
                    record.enrolled
                    and (record.netid not in signed_up_users)
                    and self.should_ping(record)
                ):

                    if debug:
                        logger(
                            f"DEBUG: Not pinging {record.netid} "
                            "for not signing up for a group"
                        )
                    else:
                        recv_email = f"{record.netid}@cornell.edu"
                        email_body = email_template.replace(
                            "<first_name>", record.first_name
                        ).replace("<last_name>", record.last_name)

                        mailer = Mailer(self.configs.send_email)
                        mailer.send(
                            recipient=recv_email,
                            subject=self.configs.subject,
                            body=email_body,
                        )
                        record.last_group_ping = datetime.now()
                        logger(
                            f"Emailed {record.netid} about not "
                            "being signed-up for a group"
                        )
