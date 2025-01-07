"""Remove unenrolled users from GitHub.

Author: Aidan McNay
Date: September 17th, 2024
"""

import github
from threading import Lock
from typing import Any, Callable, Self

from github_steps import _github, _org
from flow.flow_steps import FlowPropagateStep
from records.student_record import StudentRecord

# -----------------------------------------------------------------------------
# RemoveUnenrolled
# -----------------------------------------------------------------------------


class RemoveUnenrolled(FlowPropagateStep[StudentRecord]):
    """A propagate step to remove unenrolled users from GitHub."""

    description = "Remove dropped students from GitHub"

    config_types = [
        (
            "staff_team",
            str,
            (
                "The name of the staff team in the GitHub org, "
                "to sanity-check we never remove staff"
            ),
        ),
    ]

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        return

    def is_staff(self: Self, user: github.NamedUser.NamedUser) -> bool:
        """Return whether the user is a staff member.

        Args:
            self (Self): The relevant propagate step
            user (github.NamedUser.NamedUser): The user to check

        Returns:
            bool: Whether the user is a staff member
        """
        return (
            user in _org.get_team_by_slug(self.configs.staff_team).get_members()
        )

    def propagate_records(
        self: Self,
        records: list[tuple[StudentRecord, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Remove students with unenrolled records from GitHub.

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
        members = _org.get_members()
        outside_collaborators = _org.get_outside_collaborators()
        invitations = _org.invitations()

        for record, lock in records:
            with lock:
                if (
                    not record.enrolled
                    and (record.github_username is not None)
                    and (record.github_valid)
                    and (record.sent_invite)
                ):
                    if debug:
                        logger(
                            f"DEBUG: Avoiding removing {record.netid} "
                            "from the GitHub org"
                        )
                        continue
                    # Remove the student, including membership, outside
                    # collaborators, and invitations
                    try:
                        user = _github.get_user(record.github_username)

                        # Only operate on NamedUsers, not AuthenticatedUsers
                        if isinstance(
                            user,
                            github.AuthenticatedUser.AuthenticatedUser,
                        ):
                            logger(f"Avoiding removing {user.login} (yourself)")
                            continue

                        if self.is_staff(user):
                            logger(
                                f"Avioding removing '{record.netid}' from "
                                "GitHub (staff member)"
                            )
                            continue
                        removed = False
                        if user in members:
                            _org.remove_from_members(user)
                            removed = True
                        if user in outside_collaborators:
                            _org.remove_outside_collaborator(user)
                            removed = True
                        if user in invitations:
                            _org.cancel_invitation(user)
                            removed = True
                        record.sent_invite = False
                        record.github_accepted = None
                        record.added_to_personal = False
                        record.added_to_group = False
                        if removed:
                            logger(f"Removed {record.netid} from GitHub")
                        else:
                            # Assume they have already been removed
                            pass
                    except Exception:
                        logger(
                            f"Issue removing {record.netid} from GitHub"
                            " - will try again later"
                        )
