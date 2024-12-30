#!/usr/bin/env python
"""A basic flow to access and manipulate integer records.

Author: Aidan McNay
Date: December 29th, 2024
"""

from utils.basic_steps import (
    BasicRecordStorer,
    BasicRecordStep,
    BasicUpdateStep,
    BasicPropagateStep,
)
from flow.flow import Flow
from flow.run_flow import run_flow

# -----------------------------------------------------------------------------
# Define our flow
# -----------------------------------------------------------------------------

basic_flow = Flow(
    name="basic-flow",
    description=("A basic flow to access and manipulate integer records"),
    record_storer_type=BasicRecordStorer,
    record_storer_name="basic-storer",
)

basic_flow.add_record_step("new-integer", BasicRecordStep)

basic_flow.add_update_step("increment-1", BasicUpdateStep)
basic_flow.add_update_step("increment-2", BasicUpdateStep)
basic_flow.add_update_step(
    "increment-3", BasicUpdateStep, depends_on=["increment-2"]
)

basic_flow.add_propagate_step("print-sum", BasicPropagateStep)

# -----------------------------------------------------------------------------
# Main Program
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    run_flow(basic_flow)
