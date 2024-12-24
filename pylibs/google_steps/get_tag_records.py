"""Looks at existing StudentRecords in a spreadsheet to generate TagRecords.

Author: Aidan McNay
Date: September 19th, 2024
"""

from typing import Any, Callable, Generic, get_args, Self, TypeVar

from flow.admin_step import AdminRecordStep
from google_steps import _sheets
from google_steps.spreadsheet_storer import SpreadsheetStorer
from records.student_record import StudentRecord
from records.tag_record import TagRecords
from utils.api_call import retry_call

# -----------------------------------------------------------------------------
# GetTagRecords
# -----------------------------------------------------------------------------

# Our record step can operate on any TagRecords
RecordType = TypeVar("RecordType", bound=TagRecords)


class GetTagRecords(Generic[RecordType], AdminRecordStep[RecordType]):
    """Get TagRecords from a spreadsheet containing StudentRecords."""

    description = (
        "Use a spreadsheet with StudentRecord representations to "
        "make TagRecords for the repos"
    )

    config_types = [
        ("sheet_id", str, "The ID of the Google Sheet to access"),
        ("tab", str, "The tab to access for student records"),
    ]

    def validate(self: Self) -> None:
        """Validate the configurations for the spreadsheet storer.

        Args:
            self (Self): The step to validate
        """
        # Make sure we can connect to the spreadsheet
        try:
            retry_call(_sheets.open_by_key, self.configs.sheet_id)
        except Exception:
            raise Exception(
                "Couldn't access spreadsheet - make sure it is "
                "shared to the service account"
            )

    def new_records(
        self: Self,
        curr_records: list[RecordType],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> list[RecordType]:
        """Add any new records to the list of records.

        Args:
            curr_records (list[RecordType]): The current list of records
            logger (Callable[[str], None]): A function to log any notable
              events
            debug (bool, optional): Whether we are in "debug" mode. In debug
              mode, no external state should be modified, and we are free to
              inject dummy information. Defaults to False.

        Returns:
            list[RecordType]: The possibly augmented list of records
        """
        curr_repos = [record.repo_name for record in curr_records]
        sheet_storer = SpreadsheetStorer[StudentRecord](
            {"sheet_id": self.configs.sheet_id, "tab": self.configs.tab}
        )
        student_records = sheet_storer.get_records(logger, debug=False)

        new_repo_count = 0

        # Hacky way to get the generic data type
        record_type = get_args(self.__orig_class__)[0]  # type: ignore

        for record in student_records:
            # Add personal repos
            if (record.personal_repo_name is not None) and (
                record.personal_repo_name not in curr_repos
            ):
                curr_records.append(
                    record_type(
                        repo_name=record.personal_repo_name,
                        repo_type="personal",
                    )
                )
                curr_repos.append(record.personal_repo_name)
                new_repo_count += 1

            # Add group repos
            if (record.group_repo_name is not None) and (
                record.group_repo_name not in curr_repos
            ):
                curr_records.append(
                    record_type(
                        repo_name=record.group_repo_name, repo_type="group"
                    )
                )
                curr_repos.append(record.group_repo_name)
                new_repo_count += 1

        if new_repo_count > 0:
            logger(f"Creating TagRecords for {new_repo_count} new repos")
        else:
            logger("No repos without a TagRecords detected")

        return curr_records
