"""A propagate step to tag a repository.

Author: Aidan McNay
Date: September 19th, 2024
"""

from datetime import datetime
from threading import Lock
from typing import Any, Callable, Literal, Self, Type, TypeVar

from flow.admin_step import AdminPropagateStep
from github_steps import _org
from records.tag_record import TagRecords

# -----------------------------------------------------------------------------
# get_tagger
# -----------------------------------------------------------------------------

tag_msg = """ECE 2300 Staff Tag
This is a lab submission.

WARNING: Manipulation of this tag is an Academic Integrity violation."""

RecordType = TypeVar("RecordType", bound=TagRecords)


def get_tagger(
    lab: str,
    repo_type: Literal["personal", "group"],
    tag_records_type: Type[RecordType],
) -> Type[AdminPropagateStep[RecordType]]:
    """Return a class that tags a specific lab.

    Args:
        lab (str): The lab to tag for.
        repo_type (Literal['personal', 'group']): The type of repo to tag
        tag_records_type: The type of TagRagords to operate on

    Returns:
        Type[AdminPropagateStep[TagRecords]]: The generated class to tag the
          lab
    """

    class RepoTagger(AdminPropagateStep[RecordType]):
        """A class to tag a specific lab submission."""

        lab_to_tag = lab
        type_to_tag = repo_type

        description = f"A step to tag submissions for {lab}"

        config_types = [
            ("tag_name", str, "What to name the tag"),
            (
                "deadline",
                datetime,
                (
                    "The deadline for the lab. The tagger will"
                    "tag repos whenever it is run after this"
                ),
            ),
        ]

        def validate(self: Self) -> None:
            """Validate the configurations for the spreadsheet storer.

            Args:
                self (Self): The step to validate
            """
            # If we could, we would validate that our lab is an actual
            # attribute in the TagRecords; however, since we don't have
            # a concrete type, we can't
            return

        def should_tag(self: Self) -> bool:
            """Determine whether to tag the repos.

            Args:
                self (Self): The relevant propagate step

            Returns:
                bool: Whether to tag the repos
            """
            # Don't ping before the scheduled date
            now = datetime.now()
            if now < self.configs.deadline:
                return False
            return True

        def propagate_records(
            self: Self,
            records: list[tuple[RecordType, Lock]],
            logger: Callable[[str], None],
            get_metadata: Callable[[str], Any],
            set_metadata: Callable[[str, Any], None],
            debug: bool = False,
        ) -> None:
            """Update our records with any new information.

            Args:
                records (list[RecordType]): The list of records to manipulate
                logger (Callable[[str], None]): A function to log any notable
                  events
                get_metadata (Callable[[str], Any],): A function to retrieve
                  global metadata previously set in the flow
                debug (bool, optional): Whether we are in "debug" mode. In debug
                  mode, no external state should be modified, and we are free to
                  inject dummy information. Defaults to False.
            """
            if not self.should_tag():
                return
            for record, lock in records:
                with lock:
                    tag_record = getattr(record, self.lab_to_tag)
                    if (not tag_record.tagged()) and (
                        record.repo_type == self.type_to_tag
                    ):
                        if debug:
                            logger(
                                f"DEBUG: Avoiding tagging {record.repo_name}"
                            )
                        else:
                            try:
                                # Need to tag the repo
                                repo = _org.get_repo(record.repo_name)
                                tag_name = self.configs.tag_name

                                # Get the current hash
                                curr_branch = repo.get_branch("main")

                                # Create the tag
                                tag = repo.create_git_tag(
                                    tag=tag_name,
                                    message=tag_msg,
                                    object=curr_branch.commit.sha,
                                    type="commit",
                                )

                                # Create a reference to the tag
                                repo.create_git_ref(
                                    "refs/tags/{}".format(tag.tag), tag.sha
                                )

                                # Update the record
                                tag_record.name = tag_name
                                tag_record.time = datetime.now()
                                tag_record.ref_sha = tag.sha
                                tag_record.commit_sha = curr_branch.commit.sha
                                logger(
                                    f"Tagged {record.repo_name} with {tag_name}"
                                )
                            except Exception:
                                logger(f"Issue tagging {record.repo_name}")

    return RepoTagger
