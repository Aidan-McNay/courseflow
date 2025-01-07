#!/usr/bin/env python
"""A top-level flow runner to manage the ECE 6745 course.

Author: Aidan McNay
Date: January 7th, 2025
"""

# Include the implemented flows in our path
import os
import sys

curr_dir = os.path.dirname(os.path.realpath(__file__))
flow_dir = os.path.join(curr_dir, "flows")
sys.path.append(flow_dir)

# -----------------------------------------------------------------------------
# Import the FlowManager and all needed flows/schedules
# -----------------------------------------------------------------------------

from flow.flow_manager import FlowManager

from access_flow import access_flow
from flow.schedule import Always

# -----------------------------------------------------------------------------
# Create the FlowManager, and add all necessary flows
# -----------------------------------------------------------------------------

ece6745_flow_manager = FlowManager(num_processes=4)

ece6745_flow_manager.add_unconf_flow(
    access_flow,
    Always(),
    (
        "/home/acm289/cornell-canvas/classes/ece6745-2025s/configs"
        "/access_flow_configs.yaml"
    ),
    silent=False,
)

# -----------------------------------------------------------------------------
# Run the manager
# -----------------------------------------------------------------------------

ece6745_flow_manager.run()
