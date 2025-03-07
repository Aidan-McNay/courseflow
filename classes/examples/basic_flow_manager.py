#!/usr/bin/env python
"""A basic flow manager to run the basic flow.

Author: Aidan McNay
Date: January 6th, 2024
"""

from basic_flow import basic_flow
from flow.flow_manager import FlowManager
from flow.schedule import Always

# -----------------------------------------------------------------------------
# Create a new FlowManager, and add basic_flow
# -----------------------------------------------------------------------------

basic_flow_manager = FlowManager(num_processes=4)

basic_flow_manager.add_unconf_flow(
    basic_flow, Always(), "./configs/basic-flow-configs.yaml", silent=False
)

# -----------------------------------------------------------------------------
# Run the manager
# -----------------------------------------------------------------------------

basic_flow_manager.run()
