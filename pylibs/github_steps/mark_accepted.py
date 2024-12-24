"""Mark users that are in the GitHub organization.

Author: Aidan McNay
Date: September 17th, 2024
"""

from threading import Lock
from typing import Any, Callable, Self

from github_steps import _org
from flow.admin_step import AdminUpdateStep
from records.student_record import StudentRecord

# -----------------------------------------------------------------------------
# MarkAccepted
# -----------------------------------------------------------------------------


class MarkAccepted(AdminUpdateStep[StudentRecord]):
    """An update step to mark students who have accepted a GitHub invite."""

    description = "Check and update students who have joined the GitHub org"

    config_types = [
        (
            "staff_team",
            str,
            (
                "The name of the staff team in the GitHub org. "
                "All members not in this are students"
            ),
        )
    ]

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        # Make sure that the staff team exists
        try:
            _org.get_team_by_slug(self.configs.staff_team)
        except Exception:
            raise Exception(f"No staff team '{self.configs.staff_team}'")

    def list_students(self: Self) -> list[str]:
        """List the student users who have joined the organization.

        Args:
            self (Self): The relevant update step

        Returns:
            list[str]: The students who have joined the GitHub org
        """
        staff_users = _org.get_team_by_slug(
            self.configs.staff_team
        ).get_members()
        return [
            user.login for user in _org.get_members() if user not in staff_users
        ]

    def update_records(
        self: Self,
        records: list[tuple[StudentRecord, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Update our records with students' acceptance to the GitHub org.

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
        lower_usernames = [name.lower() for name in self.list_students()]
        for record, lock in records:
            with lock:
                if record.github_accepted is not True:
                    if (
                        (record.github_valid is True)
                        and (record.github_username is not None)
                        and (record.github_username.lower() in lower_usernames)
                    ):
                        logger(
                            f"{record.netid} ({record.github_username}) "
                            "joined on GitHub"
                        )
                        record.github_accepted = True
