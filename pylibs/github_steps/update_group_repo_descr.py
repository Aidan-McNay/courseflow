"""Update group repos' descriptions with the names of students who have access.

Author: Aidan McNay
Date: January 7th, 2025
"""

import re
from threading import Lock
from typing import Any, Callable, Self, Type

from github_steps import _org
from flow.flow_steps import FlowPropagateStep, ValidConfigTypes
from records.student_record import StudentRecord

# -----------------------------------------------------------------------------
# AddToGroupRepos
# -----------------------------------------------------------------------------


class UpdateGroupRepoDescr(FlowPropagateStep[StudentRecord]):
    """A propagate step to update group repo descriptions."""

    description = "Update the descriptions of group repos based on membership"

    config_types: list[tuple[str, Type[ValidConfigTypes], str]] = [
        (
            "repo_regex",
            str,
            (
                "The regex to identify repos to modify. "
                "Only repositories with names matching the regex "
                "will be modified. "
                "Use single quotes to specify"
            ),
        )
    ]

    def validate(self: Self) -> None:
        """Validate the configurations for the step."""
        # Make sure that we can parse the regex
        re.compile(r"{}".format(self.configs.repo_regex))
        return

    def should_change_descr(self: Self, repo_name: str) -> bool:
        """Determine whether to modify the repo's description.

        Args:
            repo_name (str): The name of the repo

        Returns:
            bool: Whether to modify the description
        """
        return (
            re.match(r"{}".format(self.configs.repo_regex), repo_name)
            is not None
        )

    def propagate_records(
        self: Self,
        records: list[tuple[StudentRecord, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Add students to their group repositories.

        We also look at the metadata 'old_groups' to remove users from
        previous groups.

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
        # Get a mapping of repo names to students who have access
        repo_name_mapping: dict[str, list[str]] = {}

        # Get the students who should be in each repo
        for record, lock in records:
            with lock:
                if (
                    record.enrolled
                    and record.group_repo_name
                    and record.added_to_group
                ):
                    if record.group_repo_name in repo_name_mapping:
                        repo_name_mapping[record.group_repo_name].append(
                            f"{record.first_name} {record.last_name} "
                            f"({record.netid})"
                        )
                    else:
                        repo_name_mapping[record.group_repo_name] = [
                            f"{record.first_name} {record.last_name} "
                            f"({record.netid})"
                        ]

        # Update repo descriptions as needed:
        for repo in _org.get_repos():
            if self.should_change_descr(repo.name):
                if repo.name in repo_name_mapping:
                    repo_descr = ", ".join(repo_name_mapping[repo.name])
                else:
                    repo_descr = "No current membership"
                if repo_descr != repo.description:
                    if debug:
                        logger(
                            "DEBUG: Avoiding updating description of "
                            f"'{repo.name}'"
                        )
                    else:
                        try:
                            repo.edit(description=repo_descr)
                            logger(
                                f"Updated description of '{repo.name}' to "
                                f"'{repo_descr}'"
                            )
                        except Exception:
                            logger(f"Error updating description of {repo.name}")
