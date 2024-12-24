#!/usr/bin/env python
"""A script to tag submissions for specific labs on specific dates.

Author: Aidan McNay
Date: September 19th, 2024
"""

from flow.admin_flow import AdminFlow
from flow.run_flow import run_flow
from github_steps.tag_repo import get_tagger
from google_steps.get_tag_records import GetTagRecords
from google_steps.spreadsheet_storer import SpreadsheetStorer
from records.tag_record import TagRecords, get_tag_headers

# -----------------------------------------------------------------------------
# Define our flow
# -----------------------------------------------------------------------------


class LabTagRecords(TagRecords):
    """Define our labs to keep track of."""

    labs = [
        "lab1.1",
        "lab1.2",
        "lab2a",
        "lab2b",
        "lab3a",
        "lab3b",
        "lab4a",
        "lab4b",
        "lab4c",
    ]
    headers = get_tag_headers(labs)


access_flow = AdminFlow(
    name="tag-flow",
    description=("A flow to tag repository submissions."),
    record_storer_type=SpreadsheetStorer[LabTagRecords],
    record_storer_name="spreadsheet-storer",
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Record Steps
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

access_flow.add_record_step("get-repos", GetTagRecords[LabTagRecords])

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Update Steps
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Propagate Steps
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Personal repo tagging
access_flow.add_propagate_step(
    "tag-lab1.1", get_tagger("lab1.1", "personal", LabTagRecords)
)
access_flow.add_propagate_step(
    "tag-lab1.2", get_tagger("lab1.2", "personal", LabTagRecords)
)

# Group repo tagging
access_flow.add_propagate_step(
    "tag-lab2a", get_tagger("lab2a", "group", LabTagRecords)
)
access_flow.add_propagate_step(
    "tag-lab2b", get_tagger("lab2b", "group", LabTagRecords)
)
access_flow.add_propagate_step(
    "tag-lab3a", get_tagger("lab3a", "group", LabTagRecords)
)
access_flow.add_propagate_step(
    "tag-lab3b", get_tagger("lab3b", "group", LabTagRecords)
)
access_flow.add_propagate_step(
    "tag-lab4a", get_tagger("lab4a", "group", LabTagRecords)
)
access_flow.add_propagate_step(
    "tag-lab4b", get_tagger("lab4b", "group", LabTagRecords)
)
access_flow.add_propagate_step(
    "tag-lab4c", get_tagger("lab4c", "group", LabTagRecords)
)

# -----------------------------------------------------------------------------
# Main Program
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    run_flow(access_flow)
