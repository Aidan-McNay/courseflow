"""A wrapper around a flow to parse arguments and run the flow.

Author: Aidan McNay
Date: September 16th, 2024
"""

import argparse
from typing import TypeVar
import yaml

from flow.flow import Flow

# -----------------------------------------------------------------------------
# run_flow
# -----------------------------------------------------------------------------
# A wrapper around a flow to run it as a main script

RecordType = TypeVar("RecordType")


def run_flow(flow: Flow[RecordType]) -> None:
    """Run a flow as a main script.

    Args:
        flow (Flow): The flow to run
    """
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Define Arguments
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    parser = argparse.ArgumentParser(
        description=f"{flow.name}: {flow.description}",
        epilog="Generated by 'run_flow'",
        add_help=False,
    )

    flow_args = parser.add_argument_group("Flow Arguments")
    flow_args.add_argument(
        "-d",
        "--dump",
        help=(
            "Dump a YAML file with documentation for "
            "the expected configurations"
        ),
        action="store",
        metavar="YAML_FILE",
    )
    flow_args.add_argument(
        "-r",
        "--run",
        help="Run the flow with the specified YAML file as configurations",
        action="store",
        metavar="YAML_FILE",
    )
    flow_args.add_argument(
        "-v",
        "--validate",
        help="Validate the flow (populate configurations, but don't run)",
        action="store",
        metavar="YAML_FILE",
    )
    flow_args.add_argument(
        "-l",
        "--logfile",
        help="A logfile to log results to",
        action="append",
        metavar="LOGFILE",
    )

    other_args = parser.add_argument_group("Other Arguments")
    other_args.add_argument(
        "-s",
        "--silent",
        help="Disable logging on the command line",
        action="store_true",
    )
    other_args.add_argument(
        "-h", "--help", help="Show this message and exit", action="help"
    )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Parse Arguments
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    GREEN = "\033[1;32m"
    RESET = "\033[0m"

    args = parser.parse_args()
    if args.silent:
        flow.silent()
    if args.logfile:
        for logfile in args.logfile:
            flow.logfile(logfile)

    if args.dump:
        with open(args.dump, "w") as f:
            yaml.dump(flow.describe_config(), f)

    elif args.validate:
        with open(args.validate, "r") as f:
            configs = yaml.safe_load(f)
        flow.config(configs)
        print(f"{GREEN}Validated, ready to deploy!{RESET}")

    elif args.run:
        with open(args.run, "r") as f:
            configs = yaml.safe_load(f)
        flow.config(configs)
        flow.run()

    else:
        print("No jobs to run!")
