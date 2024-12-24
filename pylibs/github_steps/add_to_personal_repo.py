"""Add students to their personal repositories.

Author: Aidan McNay
Date: September 18th, 2024
"""

import github
from threading import Lock
from typing import Any, Callable, Self, Type

from github_steps import _github, _org
from flow.admin_step import AdminPropagateStep, ValidConfigTypes
from records.student_record import StudentRecord

# -----------------------------------------------------------------------------
# AddToPersonalRepos
# -----------------------------------------------------------------------------


class AddToPersonalRepos(AdminPropagateStep[StudentRecord]):
    """A propagate step to give students permission to their personal repos."""

    description = "Give students access to their personal repos"

    config_types: list[tuple[str, Type[ValidConfigTypes], str]] = []

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        return

    def propagate_records(
        self: Self,
        records: list[tuple[StudentRecord, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Add students to their personal repositories.

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
        for record, lock in records:
            with lock:
                if (
                    record.enrolled
                    and record.github_accepted
                    and (not record.added_to_personal)
                    and (record.personal_repo_name is not None)
                ):
                    if record.github_username is None:
                        logger(
                            f"{record.netid} accepted to GitHub, "
                            "but no username; ignoring"
                        )
                        continue
                    if debug:
                        logger(
                            f"DEBUG: Not adding {record.netid} to personal repo"
                        )
                        continue
                    try:
                        repo = _org.get_repo(record.personal_repo_name)
                        user = _github.get_user(record.github_username)

                        # Only operate on NamedUsers, not AuthenticatedUsers
                        if isinstance(
                            user,
                            github.AuthenticatedUser.AuthenticatedUser,
                        ):
                            logger(
                                f"Avoiding inviting {user.login} (yourself?)"
                            )
                            continue
                        repo.add_to_collaborators(
                            collaborator=user, permission="push"
                        )
                        record.added_to_personal = True
                        logger(f"{record.netid} added to personal repo")
                    except Exception:
                        logger(f"Error adding {record.netid} to personal repo")
