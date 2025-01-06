"""One manager to bring them all and in the darkness bind them.

Author: Aidan McNay
Date: January 6th, 2025
"""

from typing import Any, ParamSpec, TypeVar
import yaml

from flow.flow import Flow
from flow.schedule import Schedule

# -----------------------------------------------------------------------------
# ManagerProcess
# -----------------------------------------------------------------------------
# Run flows in different processes if dill is available
#
# Reference: https://stackoverflow.com/a/72776044

P = ParamSpec("P")
T = TypeVar("T")

try:
    import pathos

    pathos_found = True

except Exception:

    pathos_found = False


# -----------------------------------------------------------------------------
# FlowManager
# -----------------------------------------------------------------------------


def _run_flow(flow: Flow[Any]) -> None:
    """Run a flow (to be used in an isolated process).

    Args:
        flow (Flow): The flow to run
    """
    if pathos_found:
        print(
            f"Running {flow.name} on "
            f"{pathos.helpers.mp.current_process().name}..."
        )
    else:
        print(f"Running {flow.name}...")
    flow.run()


class FlowManager:
    """A manager to run many flows on predetermined schedules."""

    def __init__(self: "FlowManager", num_processes: int) -> None:
        """Initialize the manager with no flows.

        Args:
            num_processes (int):
              The number of processes to use when running flows.
        """
        self.flows: list[tuple[Flow[Any], Schedule]] = []
        self.num_processes = num_processes

    def _check_if_added(self: "FlowManager", flow: Flow[Any]) -> None:
        """Check that a flow hasn't already been added.

        Args:
            flow (Flow[Any]): The flow to check
        """
        if flow.name in [f.name for (f, _) in self.flows]:
            raise Exception(f"Flow '{flow.name}' already added")

    def add_conf_flow(
        self: "FlowManager", flow: Flow[Any], schedule: Schedule
    ) -> None:
        """Add a configured flow to be run on a schedule.

        Args:
            flow (Flow[Any]): The configured flow to run
            schedule (Schedule): The schedule to run the flow on

        Raises:
            Exception:
              Raised if the flow isn't configured, or if a flow with the
              same name is already present
        """
        self._check_if_added(flow)
        if not flow.configured:
            raise Exception(f"Flow {flow.name} isn't already configured")
        self.flows.append((flow, schedule))

    def add_unconf_flow(
        self: "FlowManager",
        flow: Flow[Any],
        schedule: Schedule,
        config_path: str,
        logfiles: list[str] = [],
        silent: bool = True,
    ) -> None:
        """Add an unconfigured flow to be run on a schedule.

        Args:
            flow (Flow[Any]): The configured flow to run
            schedule (Schedule): The schedule to run the flow on
            config_path (str): The path to the flow's configurations
            logfiles (list[str]):
              Paths to logfiles, to record the flow's output to. Defaults to []
            silent (bool):
              Whether the flow should not print output to the terminal.
              Defaults to True

        Raises:
            Exception:
              Raised if the flow is configured, or if a flow with the
              same name is already present
        """
        self._check_if_added(flow)
        if flow.configured:
            raise Exception(f"Flow {flow.name} is already configured")
        with open(config_path, "r") as f:
            configs = yaml.safe_load(f)

        flow.config(configs)
        for logfile in logfiles:
            flow.logfile(logfile)
        if silent:
            flow.silent()
        else:
            flow.verbose()
        self.flows.append((flow, schedule))

    def run(self: "FlowManager") -> None:
        """Run the flow manager.

        This will check the schedules of all flows, and run them if
        appropriate (each on a separate process).
        """
        flows_to_run: list[Flow[Any]] = []
        for flow, schedule in self.flows:
            if schedule.should_run():
                flows_to_run.append(flow)

        if pathos_found:
            pool = pathos.multiprocessing.ProcessingPool(
                nodes=self.num_processes
            )
            pool.map(_run_flow, flows_to_run)

        else:
            for flow in flows_to_run:
                _run_flow(flow)
