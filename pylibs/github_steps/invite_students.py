"""Invite students to join the GitHub organization.

Author: Aidan McNay
Date: September 17th, 2024
"""

from datetime import datetime
import github
from threading import Lock
from typing import Any, Callable, Self

from github_steps import _github, _org
from flow.admin_step import AdminPropagateStep
from records.student_record import StudentRecord

# -----------------------------------------------------------------------------
# InviteStudents
# -----------------------------------------------------------------------------


class InviteStudents(AdminPropagateStep[StudentRecord]):
    """Invite students to join the GitHub organization."""

    description = "Invite students to join the GitHub organization"

    config_types = [
        (
            "student_team",
            str,
            ("The name of the student team in the GitHub org."),
        ),
    ]

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        # Make sure that the student team exists
        try:
            _org.get_team_by_slug(self.configs.student_team)
        except Exception:
            raise Exception(f"No student team '{self.configs.student_team}'")

    def propagate_records(
        self: Self,
        records: list[tuple[StudentRecord, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Invite students to join the GitHub organization.

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
        student_team = _org.get_team_by_slug(self.configs.student_team)

        for record, lock in records:
            with lock:
                if (
                    record.enrolled
                    and record.github_valid
                    and (record.github_username is not None)
                    and (not record.sent_invite)
                ):
                    if debug:
                        logger(
                            f"DEBUG: Avoiding adding {record.netid} "
                            "to the GitHub org."
                        )
                    else:
                        try:
                            user = _github.get_user(record.github_username)

                            # Only operate on NamedUsers, not AuthenticatedUsers
                            if isinstance(
                                user,
                                github.AuthenticatedUser.AuthenticatedUser,
                            ):
                                logger(
                                    f"Avoiding inviting {user.login} "
                                    "(yourself?)"
                                )
                                continue

                            _org.invite_user(
                                user=user,
                                role="direct_member",
                                teams=[student_team],
                            )
                            record.sent_invite = True
                            record.invite_date = datetime.now()
                            record.github_accepted = False
                            logger(f"Invited {record.netid} to the GitHub org")
                        except Exception:
                            logger(
                                f"Issue inviting {record.netid} "
                                "to the GitHub org"
                            )
