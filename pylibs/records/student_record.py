"""A representation of a student's record.

This is to keep track of their status through and across runs.

Author: Aidan McNay
Date: September 14th, 2024
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, NotRequired, Type, TypeVar, TypedDict

from records.spreadsheet_record import SpreadsheetRecord

# -----------------------------------------------------------------------------
# StudentRecord
# -----------------------------------------------------------------------------
# A record representing a student

# Use a type variable to represent this class and all children
StudentRecordChild = TypeVar("StudentRecordChild", bound="StudentRecord")

# Use a TypedDict to pass in arguments
StudentRecordAttrs = TypedDict(
    "StudentRecordAttrs",
    {
        "first_name": str,
        "last_name": str,
        "netid": str,
        "cuid": str,
        "enrolled": NotRequired[bool],
        "github_username": NotRequired[Optional[str]],
        "github_valid": NotRequired[Optional[bool]],
        "last_no_username_ping": NotRequired[Optional[datetime]],
        "last_valid_ping": NotRequired[Optional[datetime]],
        "sent_invite": NotRequired[bool],
        "invite_date": NotRequired[Optional[datetime]],
        "github_accepted": NotRequired[Optional[bool]],
        "last_accepted_ping": NotRequired[Optional[datetime]],
        "personal_repo_name": NotRequired[Optional[str]],
        "added_to_personal": NotRequired[bool],
        "last_group_ping": NotRequired[Optional[datetime]],
        "group_num": NotRequired[Optional[int]],
        "group_repo_name": NotRequired[Optional[str]],
        "added_to_group": NotRequired[bool],
    },
)


@dataclass
class StudentRecord(SpreadsheetRecord):
    """A record indicating a student's status in the class.

    This includes metadata about the student, as well as
    attributes reflecting whether specific activities have been
    completed.

    Attributes:
     - first_name (str): The student's first name
     - last_name (str): The student's last name
     - netid (str): The student's NetID
     - cuid (str): The student's CUID
     - enrolled (bool): Whether the student is still enrolled or not
     - github_username (Optional[str]):
         The student's GitHub username, if known
     - github_valid (Optional[bool]):
         Whether their GitHub username is valid
     - last_no_username_ping (Optional[datetime.datetime]):
         When they were last pinged about not submitting a GitHub username
     - last_valid_ping (Optional[datetime.datetime]):
         When they were last pinged about their invalid GitHub username,
         if at all
     - sent_invite (bool):
         Whether they've been sent a GitHub invitation
     - invite_date (Optional[datetime.datetime]):
         When they were sent a GitHub invitation
     - github_accepted (bool):
         Whether they've accepted their GitHub invite
     - last_accepted_ping (Optional[datetime.datetime]):
         When they were last pinged to accept the GitHub invite, if at all
     - personal_repo_name (Optional[str]):
         The name of their personal GitHub repository
     - added_to_personal (bool):
         Whether they've been added to their personal GitHub repository
     - group_num (Optional[str]):
         The number of their lab group on Canvas
     - group_repo_name (Optional[str]):
         The name of their lab group's repo on GitHub
     - added_to_group (bool):
         Whether they've been added to their lab group's repo on GitHub
    """

    first_name: str
    last_name: str
    netid: str
    cuid: str
    enrolled: bool = True
    github_username: Optional[str] = None
    github_valid: Optional[bool] = None
    last_no_username_ping: Optional[datetime] = None
    last_valid_ping: Optional[datetime] = None
    sent_invite: bool = False
    invite_date: Optional[datetime] = None
    github_accepted: Optional[bool] = None
    last_accepted_ping: Optional[datetime] = None
    personal_repo_name: Optional[str] = None
    added_to_personal: bool = False
    last_group_ping: Optional[datetime] = None
    group_num: Optional[int] = None
    group_repo_name: Optional[str] = None
    added_to_group: bool = False

    # -------------------------------------------------------------------------
    # Support for spreadsheet representation
    # -------------------------------------------------------------------------

    headers = [
        "First Name",
        "Last Name",
        "NetID",
        "CUID",
        "Enrolled?",
        "GithubUsername",
        "ValidUsername?",
        "LastUsernamePing",
        "LastValidPing",
        "SentInvite?",
        "InviteDate",
        "GithubAccepted?",
        "LastAcceptedPing",
        "PersonalRepoName",
        "AddedToPersonal?",
        "LastGroupPing",
        "GroupNum",
        "GroupRepoName",
        "AddedToGroup?",
    ]

    def to_strings(self: "StudentRecord") -> list[str]:
        """Represent the record as a list of strings.

        This is used to store the record in a spreadsheet.

        Returns:
            list[str]: The strings that represent the record
        """

        def opt_attr(value: Optional[str | int | bool]) -> str:
            """Convert an optional string to a string."""
            return "" if value is None else str(value)

        def opt_datetime_attr(value: Optional[datetime]) -> str:
            """Convert an optional datetime to a string."""
            return "" if value is None else value.strftime("%Y-%m-%d %H:%M")

        record_map = {
            "First Name": self.first_name,
            "Last Name": self.last_name,
            "NetID": self.netid,
            "CUID": self.cuid,
            "Enrolled?": str(self.enrolled),
            "GithubUsername": opt_attr(self.github_username),
            "ValidUsername?": opt_attr(self.github_valid),
            "LastUsernamePing": opt_datetime_attr(self.last_no_username_ping),
            "LastValidPing": opt_datetime_attr(self.last_valid_ping),
            "SentInvite?": str(self.sent_invite),
            "InviteDate": opt_datetime_attr(self.invite_date),
            "GithubAccepted?": opt_attr(self.github_accepted),
            "LastAcceptedPing": opt_datetime_attr(self.last_accepted_ping),
            "PersonalRepoName": opt_attr(self.personal_repo_name),
            "AddedToPersonal?": str(self.added_to_personal),
            "LastGroupPing": opt_datetime_attr(self.last_group_ping),
            "GroupNum": opt_attr(self.group_num),
            "GroupRepoName": opt_attr(self.group_repo_name),
            "AddedToGroup?": str(self.added_to_group),
        }

        row_repr = []
        for i in range(len(self.headers)):
            row_repr.append(record_map[self.headers[i]])
        return row_repr

    @classmethod
    def from_strings(
        cls: Type[StudentRecordChild], header_mapping: dict[str, str]
    ) -> StudentRecordChild:
        """Form a StudentRecord from the data found under headers.

        This is used to obtain a record from a spreadsheet entry.

        Args:
            header_mapping (dict[str, str]): The mapping of headers to row data

        Raises:
            Exception: Raised if a mandatory header is missing

        Returns:
            StudentRecord: The corresponding record with the desired data
        """
        # First check that we have the mandatory headers
        mandatory_headers = ["First Name", "Last Name", "NetID", "CUID"]
        for header in mandatory_headers:
            if header not in header_mapping:
                raise Exception(f"Missing header '{header}' for StudentRecord")

        # From here, create the arguments
        args: StudentRecordAttrs = {
            "first_name": header_mapping["First Name"],
            "last_name": header_mapping["Last Name"],
            "netid": header_mapping["NetID"],
            "cuid": header_mapping["CUID"],
        }

        # Get all the other arguments we have
        if "Enrolled?" in header_mapping:
            args["enrolled"] = (
                True if header_mapping["Enrolled?"] == "True" else False
            )

        if "GithubUsername" in header_mapping:
            args["github_username"] = (
                None
                if len(header_mapping["GithubUsername"]) == 0
                else header_mapping["GithubUsername"]
            )

        if "ValidUsername?" in header_mapping:
            args["github_valid"] = (
                None
                if len(header_mapping["ValidUsername?"]) == 0
                else (
                    True
                    if header_mapping["ValidUsername?"] == "True"
                    else False
                )
            )

        if "LastUsernamePing" in header_mapping:
            args["last_no_username_ping"] = (
                None
                if len(header_mapping["LastUsernamePing"]) == 0
                else datetime.strptime(
                    header_mapping["LastUsernamePing"], "%Y-%m-%d %H:%M"
                )
            )

        if "LastValidPing" in header_mapping:
            args["last_valid_ping"] = (
                None
                if len(header_mapping["LastValidPing"]) == 0
                else datetime.strptime(
                    header_mapping["LastValidPing"], "%Y-%m-%d %H:%M"
                )
            )

        if "SentInvite?" in header_mapping:
            args["sent_invite"] = (
                True if header_mapping["SentInvite?"] == "True" else False
            )

        if "InviteDate" in header_mapping:
            args["invite_date"] = (
                None
                if len(header_mapping["InviteDate"]) == 0
                else datetime.strptime(
                    header_mapping["InviteDate"], "%Y-%m-%d %H:%M"
                )
            )

        if "GithubAccepted?" in header_mapping:
            args["github_accepted"] = (
                None
                if len(header_mapping["GithubAccepted?"]) == 0
                else (
                    True
                    if header_mapping["GithubAccepted?"] == "True"
                    else False
                )
            )

        if "LastAcceptedPing" in header_mapping:
            args["last_accepted_ping"] = (
                None
                if len(header_mapping["LastAcceptedPing"]) == 0
                else datetime.strptime(
                    header_mapping["LastAcceptedPing"], "%Y-%m-%d %H:%M"
                )
            )

        if "PersonalRepoName" in header_mapping:
            args["personal_repo_name"] = (
                None
                if len(header_mapping["PersonalRepoName"]) == 0
                else header_mapping["PersonalRepoName"]
            )

        if "AddedToPersonal?" in header_mapping:
            args["added_to_personal"] = (
                True if header_mapping["AddedToPersonal?"] == "True" else False
            )

        if "LastGroupPing" in header_mapping:
            args["last_group_ping"] = (
                None
                if len(header_mapping["LastGroupPing"]) == 0
                else datetime.strptime(
                    header_mapping["LastGroupPing"], "%Y-%m-%d %H:%M"
                )
            )

        if "GroupNum" in header_mapping:
            args["group_num"] = (
                None
                if len(header_mapping["GroupNum"]) == 0
                else int(header_mapping["GroupNum"])
            )

        if "GroupRepoName" in header_mapping:
            args["group_repo_name"] = (
                None
                if len(header_mapping["GroupRepoName"]) == 0
                else header_mapping["GroupRepoName"]
            )

        if "AddedToGroup?" in header_mapping:
            args["added_to_group"] = (
                True if header_mapping["AddedToGroup?"] == "True" else False
            )

        return cls(**args)
