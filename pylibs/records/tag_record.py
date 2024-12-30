"""A representation of a repository that's been tagged.

Author: Aidan McNay
Date: September 19th, 2024
"""

# flake8: noqa D412

from dataclasses import dataclass
from datetime import datetime
from itertools import chain
from typing import Literal, Optional, Type, TypeGuard, TypeVar

from records.spreadsheet_record import SpreadsheetRecord

# -----------------------------------------------------------------------------
# TagRecord
# -----------------------------------------------------------------------------


@dataclass
class TagRecord:
    """A (possible) representation of a tag on a repository.

    A TagRecord does not have to represent a current tag; it can also
    serve as a placeholder for a tag that hasn't been created yet.

    Attributes:

     - name (Optional[str]): The name of the tag
     - time (Optional[datetime]): The time the tag was created
     - ref_sha (Optional[str]): The SHA-1 Hash of the Git Reference
     - commit_sha (Optional[str]):
         The SHA-1 Hash of the commit that the tag references
    """

    name: Optional[str] = None
    time: Optional[datetime] = None
    ref_sha: Optional[str] = None
    commit_sha: Optional[str] = None

    def tagged(self: "TagRecord") -> bool:
        """Return whether the repo has already been tagged.

        Args:
            self (TagRecord): The TagRecord which may represent a tag

        Returns:
            bool: Whether the record represents an actual tag
        """
        return self.name is not None


# -----------------------------------------------------------------------------
# TagRecords
# -----------------------------------------------------------------------------
# A representation of many TagRecord objects associated with a repository

TagRecordsChild = TypeVar("TagRecordsChild", bound="TagRecords")


def is_repo_type(
    repo_type: str,
) -> TypeGuard[Literal["personal", "group"]]:
    """Verify that our repo_type is a valid type.

    Args:
        repo_type (str): The repo_type to check

    Returns:
        _type_: The narrowed type
    """
    return repo_type in ("personal", "group")


def get_tag_headers(labs: list[str]) -> list[str]:
    """Create the headers for a TagRecords, based on its labs.

    Args:
        labs (list[str]): The labs that a TagRecords hold.

    Returns:
        list[str]:
          The corresponding spreadsheet headers that should be used to
          represent the TagRecords
    """
    lab_headers_nested = [
        [
            f"{lab}-TagName",
            f"{lab}-TagDate",
            f"{lab}-RefSHA",
            f"{lab}-CommitSHA",
        ]
        for lab in labs
    ]
    lab_headers = list(chain.from_iterable(lab_headers_nested))
    headers = ["RepoName", "RepoType"] + lab_headers
    return headers


class TagRecords(SpreadsheetRecord):
    """A collection of TagRecords for a specific repository."""

    # Users should override labs to define their own lab instances
    labs: list[str] = []

    # Users should override headers with the output of get_tag_headers
    # for their labs
    headers: list[str] = []

    def __init__(
        self: "TagRecords",
        repo_name: str,
        repo_type: Literal["personal", "group"],
    ) -> None:
        """Initialize the TagRecords for a specific repository.

        Args:
            repo_name (str): The name of the repository
            repo_type (Literal['personal', 'group']): The type of the
              repository
        """
        self.repo_name = repo_name
        self.repo_type = repo_type
        for lab in self.labs:
            setattr(self, lab, TagRecord())
        if not is_repo_type(repo_type):
            raise Exception(f"Invalid repo type: '{repo_type}'")
        if len(self.labs) == 0:
            raise Exception("Class attribute 'labs' isn't overriden!")
        if len(self.headers) == 0:
            raise Exception("Class attributes 'headers' isn't overriden!")

    def to_strings(self: "TagRecords") -> list[str]:
        """Represent an instance of the generated class as strings.

        Args:
            self (TagRecords): An instance of the generated class

        Returns:
            list[str]: The string representation
        """

        def opt_attr(value: Optional[str | bool]) -> str:
            """Convert an optional string to a string."""
            return "" if value is None else str(value)

        def opt_datetime_attr(value: Optional[datetime]) -> str:
            """Convert an optional datetime to a string."""
            return "" if value is None else value.strftime("%Y-%m-%d %H:%M")

        record_map = {"RepoName": self.repo_name, "RepoType": self.repo_type}
        for lab in self.labs:
            record_map.update(
                {
                    f"{lab}-TagName": opt_attr(getattr(self, lab).name),
                    f"{lab}-TagDate": opt_datetime_attr(
                        getattr(self, lab).time
                    ),
                    f"{lab}-RefSHA": opt_attr(getattr(self, lab).ref_sha),
                    f"{lab}-CommitSHA": opt_attr(getattr(self, lab).commit_sha),
                }
            )

        row_repr = []
        for i in range(len(self.headers)):
            row_repr.append(record_map[self.headers[i]])
        return row_repr

    @classmethod
    def from_strings(
        cls: Type[TagRecordsChild], header_mapping: dict[str, str]
    ) -> "TagRecords":
        """Form a TagRecords from the data found under headers.

        This is used to obtain a record from a spreadsheet entry.

        Args:
            header_mapping (dict[str, str]): The mapping of headers to row data

        Raises:
            Exception: Raised if a mandatory header is missing

        Returns:
            TagRecords: The corresponding record with the desired data
        """
        mandatory_headers = ["RepoName", "RepoType"]
        for header in mandatory_headers:
            if header not in header_mapping:
                raise Exception(f"Missing header '{header}' for TagRecords")

        repo_name = header_mapping["RepoName"]
        repo_type = header_mapping["RepoType"]

        if not is_repo_type(repo_type):
            raise Exception(f"Invalid repo_type: '{repo_type}'")

        # Create the initial TagRecords
        tag_records = cls(
            repo_name=repo_name,
            repo_type=repo_type,
        )

        # Add all labs as needed
        for lab in cls.labs:
            if (
                f"{lab}-TagName" in header_mapping
                and f"{lab}-TagDate" in header_mapping
                and f"{lab}-RefSHA" in header_mapping
                and f"{lab}-CommitSHA" in header_mapping
            ):
                name_data = header_mapping[f"{lab}-TagName"]
                date_data = header_mapping[f"{lab}-TagDate"]
                ref_data = header_mapping[f"{lab}-RefSHA"]
                commit_data = header_mapping[f"{lab}-CommitSHA"]

                name = None if len(name_data) == 0 else name_data
                date = (
                    None
                    if len(date_data) == 0
                    else datetime.strptime(date_data, "%Y-%m-%d %H:%M")
                )
                ref = None if len(ref_data) == 0 else ref_data
                commit = None if len(commit_data) == 0 else commit_data

                tag_record = TagRecord(
                    name=name, time=date, ref_sha=ref, commit_sha=commit
                )
                setattr(tag_records, lab, tag_record)

        return tag_records
