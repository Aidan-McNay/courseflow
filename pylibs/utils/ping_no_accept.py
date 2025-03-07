"""Ping students who haven't accepted their GitHub invitation.

Author: Aidan McNay
Date: September 17th, 2024
"""

from datetime import datetime
import os
from threading import Lock
from typing import Any, Callable, Self

from flow.flow_steps import FlowPropagateStep
from records.student_record import StudentRecord
from utils.mailer import Mailer

# -----------------------------------------------------------------------------
# PingNoUsername
# -----------------------------------------------------------------------------


class PingNoAccept(FlowPropagateStep[StudentRecord]):
    """Ping users who haven't accepted their GitHub invitation."""

    description = "Email students who haven't accepted a GitHub org invite"

    config_types = [
        ("start_date", datetime, "When to start emailing students"),
        ("email_gap", int, "The number of days between reminder emails"),
        (
            "email_template",
            str,
            (
                "The path to the template email (text file) to send. "
                "Instances of <first_name>, <last_name>, and <username> will "
                "be replaced appropriately"
            ),
        ),
        (
            "send_email",
            str,
            "The email to send from (matching `GMAIL_API_KEY`)",
        ),
        ("subject", str, "The subject that the email should be sent with"),
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
        if record.last_accepted_ping:
            # Always round to the hour the ping happened in, to avoid random
            # drift over time
            last_ping = record.last_accepted_ping.replace(
                minute=0, second=0, microsecond=0
            )
            if (now - last_ping).days < self.configs.email_gap:
                return False

        # Also don't ping within the gap to the invitation
        if record.invite_date:
            # Always round to the hour the ping happened in, to avoid random
            # drift over time
            last_ping = record.invite_date.replace(
                minute=0, second=0, microsecond=0
            )
            if (now - last_ping).days < self.configs.email_gap:
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
        """Email students who haven't accepted their GitHub invitation.

        Args:
            records (list[RecordType]): The list of records to manipulate
            logger (Callable[[str], None]): A function to log any notable
              events
            get_metadata (Callable[[str], Any],): A function to retrieve global
              metadata previously set in the flow
            set_metadata (Callable[[str, Any], None]): A function to set
              global metadata within the flow
            debug (bool, optional): Whether we are in "debug" mode. In debug
              mode, no external state should be modified, and we are free to
              inject dummy information. Defaults to False.
        """
        with open(self.configs.email_template, "r") as f:
            email_template = f.read()

        for record, lock in records:
            with lock:
                if (
                    record.enrolled
                    and (record.sent_invite)
                    and (not record.github_accepted)
                    and self.should_ping(record)
                ):
                    if debug:
                        logger(
                            f"DEBUG: Not pinging {record.netid} "
                            "for unaccepted invite"
                        )
                    else:
                        recv_email = f"{record.netid}@cornell.edu"

                        # There will always be a username here, but use str()
                        # for type-checking
                        email_body = (
                            email_template.replace(
                                "<first_name>", record.first_name
                            )
                            .replace("<last_name>", record.last_name)
                            .replace("<username>", str(record.github_username))
                        )

                        mailer = Mailer(self.configs.send_email)
                        mailer.send(
                            recipient=recv_email,
                            subject=self.configs.subject,
                            body=email_body,
                        )
                        record.last_accepted_ping = datetime.now()
                        logger(
                            f"Emailed {record.netid} about their "
                            "unaccepted invite"
                        )
