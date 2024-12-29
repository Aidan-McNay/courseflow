"""Steps for managing and monitoring students' enrollment on Canvas.

Author: Aidan McNay
Date: September 16th, 2024
"""

from threading import Lock
from typing import Any, Callable, cast, Self

from canvas_steps import _course
from flow.flow_steps import FlowRecordStep, FlowUpdateStep, FlowPropagateStep
from records.student_record import StudentRecord
from utils.mailer import Mailer

# -----------------------------------------------------------------------------
# AddEnrollment
# -----------------------------------------------------------------------------


class AddEnrollment(FlowRecordStep[StudentRecord]):
    """A record step that adds new student records for new enrollment.

    We also set the global metadata 'new_netids' to a list of NetIDs that
    just enrolled.
    """

    description = "Add newly enrolled students from Canvas"
    config_types = []

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        return

    def new_records(
        self: Self,
        curr_records: list[StudentRecord],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> list[StudentRecord]:
        """Add any newly enrolled students to the list of records.

        Args:
            curr_records (list[StudentRecord]): The current list of records
            logger (Callable[[str], None]): A function to log any notable
              events
            debug (bool, optional): Whether we are in "debug" mode. In debug
              mode, no external state should be modified, and we are free to
              inject dummy information. Defaults to False.

        Returns:
            list[StudentRecord]: The possibly augmented list of records
        """
        enrolled_users = _course.get_users(enrollment_type="student")
        already_added_users = [record.netid for record in curr_records]

        new_netids = []
        for enrolled_user in enrolled_users:
            netid = enrolled_user.login_id
            if netid not in already_added_users:
                logger(f"New student from Canvas: '{netid}'")
                sortable_name = enrolled_user.sortable_name
                name_elements = [
                    element.strip() for element in sortable_name.split(",")
                ]

                last_name = name_elements[0]
                first_name = name_elements[1]
                cuid = enrolled_user.sis_user_id

                curr_records.append(
                    StudentRecord(first_name, last_name, netid, cuid)
                )
                new_netids.append(netid)

        set_metadata("new_netids", new_netids)
        return curr_records


# -----------------------------------------------------------------------------
# UpdateEnrollment
# -----------------------------------------------------------------------------


class UpdateEnrollment(FlowUpdateStep[StudentRecord]):
    """An update step that updates enrollment for based on Canvas.

    We also set the global metadata 'unenrolled_netids' to a list of NetIDs
    that dropped the course.
    """

    description = "Add newly enrolled students from Canvas"
    config_types = []

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        return

    def update_records(
        self: Self,
        records: list[tuple[StudentRecord, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Update our records to reflect dropped students.

        Args:
            records (list[StudentRecord]): The list of records to manipulate
            logger (Callable[[str], None]): A function to log any notable
              events
            set_metadata (Callable[[str, Any], None]): A function to set
              global metadata within the flow
            debug (bool, optional): Whether we are in "debug" mode. In debug
              mode, no external state should be modified, and we are free to
              inject dummy information. Defaults to False.
        """
        enrolled_users = _course.get_users(enrollment_type="student")
        enrolled_netids = [user.login_id for user in enrolled_users]

        unenrolled_netids = []
        for record, lock in records:
            with lock:
                # Unenroll students who have dropped
                if record.enrolled and (record.netid not in enrolled_netids):
                    logger(f"Dropped student: '{record.netid}'")
                    record.enrolled = False
                    unenrolled_netids.append(record.netid)

                # Re-enroll any students who were previously enrolled
                if not record.enrolled and (record.netid in enrolled_netids):
                    logger(f"Re-enrolled student: '{record.netid}'")
                    record.enrolled = True

                    # Mark everything else as not having access, so access is
                    # is later re-propagated
                    record.sent_invite = False
                    record.github_accepted = None
                    record.added_to_personal = False
                    record.added_to_group = False

        set_metadata("unenrolled_netids", unenrolled_netids)


# -----------------------------------------------------------------------------
# PingNewEnrollment
# -----------------------------------------------------------------------------


class PingNewEnrollment(FlowPropagateStep[StudentRecord]):
    """A propagate step to pinga user when new enrollment is detected."""

    description = "Send an email when new course enrollment is detected"
    config_types = [
        (
            "send_email",
            str,
            "The email to send from (matching `GMAIL_API_KEY`)",
        ),
        ("recv_email", str, "The email to send the notification to"),
        ("subject", str, "The subject that the email should be sent with"),
    ]

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        # Make sure that we can access the email
        try:
            Mailer(self.configs.send_email)
        except Exception:
            raise Exception(
                f"Couldn't log into '{self.configs.send_email}'"
                " - double-check your API key"
            )

    def propagate_records(
        self: Self,
        records: list[tuple[StudentRecord, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Send an email to indicate the new enrollment.

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
        new_netids = get_metadata("new_netids")
        if new_netids is None:
            return
        if not isinstance(new_netids, list):
            logger("'new_netids' is of wrong type; no ping email to send")
            return
        for netid in new_netids:
            if not isinstance(netid, str):
                logger("'new_netids' is of wrong type; no ping email to send")
                return

        # Now we know it's a list of strings
        netids_to_send = cast(list[str], new_netids)
        if len(netids_to_send) == 0:
            logger("No new enrollment to send")
            return

        if debug:
            logger("DEBUG: Not sending new enrollment")
            return

        # Send the NetIDs
        email_body = "New Enrollment Detected!\n\n"
        for netid in netids_to_send:
            email_body += f" - {netid}\n"

        mailer = Mailer(self.configs.send_email)
        mailer.send(
            recipient=self.configs.recv_email,
            subject=self.configs.subject,
            body=email_body,
        )
        logger(f"New enrollment sent to {self.configs.recv_email}")
