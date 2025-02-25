#!/usr/bin/env python
"""A script to tag submissions for specific labs on specific dates.

Author: Aidan McNay
Date: January 7th, 2025
"""

from flow.flow import Flow
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
        "lab1",
    ]
    headers = get_tag_headers(labs)


tag_flow = Flow(
    name="tag-flow",
    description=("A flow to tag repository submissions."),
    record_storer_type=SpreadsheetStorer[LabTagRecords],
    record_storer_name="spreadsheet-storer",
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Record Steps
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Need to make a tags sheet in the course database spreadsheet!

tag_flow.add_record_step("get-repos", GetTagRecords[LabTagRecords])

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Update Steps
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Propagate Steps
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Group repo tagging
tag_flow.add_propagate_step(
    "tag-lab1", get_tagger("lab1", "group", LabTagRecords)
)
# tag_flow.add_propagate_step(
#     "tag-lab2", get_tagger("lab2", "group", LabTagRecords)
# )

# -----------------------------------------------------------------------------
# Main Program
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    run_flow(tag_flow)
