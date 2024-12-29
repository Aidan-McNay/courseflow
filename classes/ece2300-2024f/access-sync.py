#!/usr/bin/env python
"""A script to sync access across the course's websites.

Author: Aidan McNay
Date: September 16th, 2024
"""

from canvas_steps.assign_groups import AssignGroups
from canvas_steps.enrollment import (
    AddEnrollment,
    UpdateEnrollment,
    PingNewEnrollment,
)
from canvas_steps.github_usernames import GitHubUsernames
from canvas_steps.ping_join_group import PingJoinGroup
from flow.flow import Flow
from flow.run_flow import run_flow
from github_steps.add_to_personal_repo import AddToPersonalRepos
from github_steps.add_to_group_repo import AddToGroupRepos
from github_steps.create_personal_repos import CreatePersonalRepos
from github_steps.create_group_repos import CreateGroupRepos
from github_steps.invite_students import InviteStudents
from github_steps.mark_accepted import MarkAccepted
from github_steps.remove_unenrolled import RemoveUnenrolled
from google_steps.spreadsheet_storer import SpreadsheetStorer
from records.student_record import StudentRecord
from utils.ping_invalid_username import PingInvalidUsername
from utils.ping_no_accept import PingNoAccept
from utils.ping_no_username import PingNoUsername

# -----------------------------------------------------------------------------
# Define our flow
# -----------------------------------------------------------------------------

access_flow = Flow(
    name="access-flow",
    description=(
        "A flow to update records and synchronize "
        "GitHub access based on Canvas"
    ),
    record_storer_type=SpreadsheetStorer[StudentRecord],
    record_storer_name="spreadsheet-storer",
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Record Steps
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

access_flow.add_record_step("add-canvas-enrollment", AddEnrollment)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Update Steps
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

access_flow.add_update_step("update-enrollment", UpdateEnrollment)
access_flow.add_update_step(
    "get-github-usernames", GitHubUsernames, depends_on=["update-enrollment"]
)
access_flow.add_update_step(
    "github-accepted", MarkAccepted, depends_on=["update-enrollment"]
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Propagate Steps
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

access_flow.add_propagate_step("assign-canvas-groups", AssignGroups)
access_flow.add_propagate_step(
    "make-group-repos", CreateGroupRepos, depends_on=["assign-canvas-groups"]
)
access_flow.add_propagate_step(
    "group-repo-permissions",
    AddToGroupRepos,
    depends_on=["make-group-repos"],
)
access_flow.add_propagate_step("make-personal-repos", CreatePersonalRepos)
access_flow.add_propagate_step("remove-dropped", RemoveUnenrolled)
access_flow.add_propagate_step("invite-students", InviteStudents)
access_flow.add_propagate_step("ping-group-join", PingJoinGroup)
access_flow.add_propagate_step("ping-enrollment", PingNewEnrollment)
access_flow.add_propagate_step("ping-invalid-username", PingInvalidUsername)
access_flow.add_propagate_step("ping-no-username", PingNoUsername)
access_flow.add_propagate_step("ping-unaccepted-invite", PingNoAccept)
access_flow.add_propagate_step(
    "personal-repo-permissions",
    AddToPersonalRepos,
    depends_on=["make-personal-repos"],
)

# -----------------------------------------------------------------------------
# Main Program
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    run_flow(access_flow)
