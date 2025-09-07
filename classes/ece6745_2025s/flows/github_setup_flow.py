#!/usr/bin/env python
"""A script to sync just the github usernames.

Author: Christopher Batten
Date: January 31, 2025
"""

from canvas_steps.assign_groups import AssignGroups
from canvas_steps.enrollment import (
    AddEnrollment,
    UpdateEnrollment,
)
from canvas_steps.github_usernames import GitHubUsernames
from canvas_steps.ping_join_group import PingJoinGroup
from flow.flow import Flow
from flow.run_flow import run_flow
from github_steps.add_to_group_repos import AddToGroupRepos
from github_steps.create_group_repos import CreateGroupRepos
from github_steps.invite_students import InviteStudents
from github_steps.mark_accepted import MarkAccepted
from github_steps.remove_unenrolled import RemoveUnenrolled
from github_steps.update_group_repo_descr import UpdateGroupRepoDescr
from google_steps.spreadsheet_storer import SpreadsheetStorer
from records.student_record import StudentRecord
from utils.ping_invalid_username import PingInvalidUsername
from utils.ping_no_accept import PingNoAccept
from utils.ping_no_username import PingNoUsername

# -------------------------------------------------------------------------
# Define our flow
# -------------------------------------------------------------------------

github_setup_flow = Flow(
    name="github-uname-flow",
    description=(
        "A flow to update records and synchronize "
        "GitHub access based on Canvas"
    ),
    record_storer_type=SpreadsheetStorer[StudentRecord],
    record_storer_name="spreadsheet-storer",
)

# AddEnrollment

github_setup_flow.add_record_step("get-students", AddEnrollment)

# GitHubUsernames

github_setup_flow.add_update_step("update-enrollment", UpdateEnrollment)
github_setup_flow.add_update_step("get-github-usernames", GitHubUsernames)
github_setup_flow.add_update_step(
    "github-accepted", MarkAccepted, depends_on=["update-enrollment"]
)

# Ping steps

github_setup_flow.add_propagate_step(
    "ping-invalid-username", PingInvalidUsername
)
github_setup_flow.add_propagate_step("ping-no-username", PingNoUsername)
github_setup_flow.add_propagate_step("invite-students", InviteStudents)
github_setup_flow.add_propagate_step("ping-unaccepted-invite", PingNoAccept)

# Propagate steps

github_setup_flow.add_propagate_step("remove-dropped", RemoveUnenrolled)

github_setup_flow.add_propagate_step("assign-canvas-groups", AssignGroups)

github_setup_flow.add_propagate_step("make-group-repos", CreateGroupRepos)

github_setup_flow.add_propagate_step(
    "group-repo-permissions",
    AddToGroupRepos,
    depends_on=["make-group-repos"],
)

github_setup_flow.add_propagate_step(
    "update-group-repo-descr",
    UpdateGroupRepoDescr,
    depends_on=["group-repo-permissions", "make-group-repos"],
)

github_setup_flow.add_propagate_step("ping-group-join", PingJoinGroup)

# -------------------------------------------------------------------------
# Main Program
# -------------------------------------------------------------------------

if __name__ == "__main__":
    run_flow(github_setup_flow)
