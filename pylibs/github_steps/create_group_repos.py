"""Create any repositories needed for individual users.

Author: Aidan McNay
Date: September 17th, 2024
"""

import os
from threading import Lock
from typing import Any, Callable, Self

from github_steps import _org
from flow.flow_steps import FlowPropagateStep
from records.student_record import StudentRecord

# -----------------------------------------------------------------------------
# CreatePersonalRepos
# -----------------------------------------------------------------------------


class CreateGroupRepos(FlowPropagateStep[StudentRecord]):
    """A propagate step to create any needed personal repos."""

    description = "Create personal repositories for students."

    config_types = [
        (
            "naming",
            str,
            (
                "The naming convention. "
                "'<num>' will be replaced appropriately."
            ),
        ),
        (
            "num_places",
            int,
            (
                "The number of places to represent the group number in "
                "the name. Ex. 2 places -> 06"
            ),
        ),
        (
            "readme_path",
            str,
            (
                "The path to the local README file, to have in the repo. "
                "'<repo_name>' will be replaced appropriately."
            ),
        ),
        ("readme_commit_msg", str, "The commit message for making the README"),
        (
            "create_upstream",
            bool,
            "Whether to create a branch named 'upstream'",
        ),
        (
            "staff_team",
            str,
            (
                "The name of the staff team in the GitHub org, "
                "to add to all personal repos"
            ),
        ),
        (
            "staff_permissions",
            str,
            (
                "The permissions to give staff members "
                "(pull, triage, push, maintain, admin)"
            ),
        ),
    ]

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        # Double-check that they replaced the filler text
        if "The commit message" in self.configs.readme_commit_msg:
            raise Exception(
                "Whoops - looks like you haven't given a README commit message!"
            )

        # Make sure that each repo will have a unique name
        if "<num>" not in self.configs.naming:
            raise Exception(
                "Whoops - make sure you have a unique name for each repo!"
            )
        # Make sure the README exists
        if not os.path.isfile(self.configs.readme_path):
            raise Exception(
                f"README file '{self.configs.readme_path}' doesn't exist"
            )

        # Make sure that the staff team exists
        try:
            _org.get_team_by_slug(self.configs.staff_team)
        except Exception:
            raise Exception(f"No staff team '{self.configs.staff_team}'")

    def create_repo(
        self: Self, repo_name: str, student_names: str, readme_text: str
    ) -> None:
        """Create a group repository.

        Args:
            self (Self): The relevant propagate step
            repo_name (str): The name of the repository to make
            student_names (str): The name of the student who the repository is
              for
            readme_text (str): The text to have in the README file
        """
        new_repo = _org.create_repo(
            name=repo_name, description=student_names, private=True
        )
        initial_commit = new_repo.create_file(
            path="README.md",
            content=readme_text,
            message=self.configs.readme_commit_msg,
        )["commit"]

        if self.configs.create_upstream:
            new_repo.create_git_ref(
                ref="refs/heads/upstream", sha=initial_commit.sha
            )

        # Add all staff members
        staff_team = _org.get_team_by_slug(self.configs.staff_team)
        staff_team.add_to_repos(new_repo)
        staff_team.set_repo_permission(new_repo, self.configs.staff_permissions)

    def propagate_records(
        self: Self,
        records: list[tuple[StudentRecord, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Create the new repositories for all students.

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
        all_repo_names = [repo.name for repo in _org.get_repos()]
        with open(self.configs.readme_path, "r") as f:
            readme_template = f.read()

        # Get the mapping of numbers to student names
        num_students_mapping: dict[int, list[str]] = {}
        for record, lock in records:
            with lock:
                if record.group_num:
                    name = f"{record.first_name} {record.last_name}"
                    if record.group_num in num_students_mapping:
                        num_students_mapping[record.group_num].append(name)
                    else:
                        num_students_mapping[record.group_num] = [name]

        # Create all the necessary repos
        for num, names in num_students_mapping.items():
            repo_name = self.configs.naming.replace(
                "<num>", str(num).zfill(self.configs.num_places)
            )
            readme_text = readme_template.replace("<repo_name>", repo_name)
            repo_exists = False
            if repo_name not in all_repo_names:
                if debug:
                    logger(f"DEBUG: Not creating group repo {repo_name}")
                else:
                    try:
                        student_names = ", ".join(names)
                        self.create_repo(repo_name, student_names, readme_text)
                        logger(f"Created group repo: '{repo_name}'")
                        repo_exists = True
                    except Exception:
                        logger(
                            f"Issue creating group repo: '{repo_name}'"
                            " - repo not created"
                        )
            else:
                repo_exists = True

            if repo_exists:
                for record, lock in records:
                    with lock:
                        if record.group_num and (record.group_num == num):
                            record.group_repo_name = repo_name
