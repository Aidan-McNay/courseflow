"""An implementation of an administrative flow that manages and executes steps.

Author: Aidan McNay
Date: September 14th, 2024
"""

from datetime import datetime
from enum import StrEnum, auto
import os
from threading import Lock, Thread
import time
from typing import (
    Any,
    cast,
    Generic,
    Optional,
    NotRequired,
    Self,
    Type,
    TypedDict,
    TypeVar,
)

from flow.flow_steps import (
    FlowRecordStep,
    FlowUpdateStep,
    FlowPropagateStep,
    ValidConfigTypes,
)
from flow.flow_logger import (
    get_logger,
    add_logfile,
    set_verbosity,
    SUCCESS,
    FLOW,
    STEP,
)
from flow.record_storer import RecordStorer

# -----------------------------------------------------------------------------
# StepMode
# -----------------------------------------------------------------------------
# The different modes that steps can run in within a flow


class StepMode(StrEnum):
    """A representation of possible modes to run steps in."""

    INCLUDE = auto()
    EXCLUDE = auto()
    DEBUG = auto()


# -----------------------------------------------------------------------------
# Flow
# -----------------------------------------------------------------------------
# The main flow that manages and executes steps

RecordType = TypeVar("RecordType")

# Define the configuration types both in the same style as steps, as well
# as a TypedDict for setting in the flow
flow_config_types: list[tuple[str, Type[ValidConfigTypes], str]] = [
    (
        "num_threads",
        int,
        (
            "The number of threads to use when "
            "running update and propagate steps"
        ),
    )
]

FlowConfigs = TypedDict(
    "FlowConfigs",
    {"num_threads": NotRequired[int]},
)


class Flow(Generic[RecordType]):
    """An administrative flow that manages and runs different sections."""

    def __init__(
        self: Self,
        name: str,
        description: str,
        record_storer_type: Type[RecordStorer[RecordType]],
        record_storer_name: str,
    ) -> None:
        """Initialize the flow with a name, description, and a RecordStorer.

        Args:
            self (Self): The flow to initialize
            name (str): The name of the flow
            description (str): A high-level description of what the flow does
            record_storer (RecordStorer[RecordType]): The storage object used
              to access and store records
            record_storer_name: The name of the record storer, to be used when
              configuring
        """
        self.name = name
        self.description = description
        self.record_storer: Optional[RecordStorer[RecordType]] = None
        self.record_storer_type = record_storer_type
        self.record_storer_name = record_storer_name
        self.configs: FlowConfigs = {}
        self.configured = False

        # Store each step as a tuple of the form
        # (
        #   name (str),
        #   step_class (Type[StepType[RecordType]]),
        #   dependencies (list[str])
        # )
        # Record steps don't have dependencies (executed sequentially)
        self.record_steps: list[
            tuple[str, Type[FlowRecordStep[RecordType]]]
        ] = []
        self.update_steps: list[
            tuple[str, Type[FlowUpdateStep[RecordType]], list[str]]
        ] = []
        self.propagate_steps: list[
            tuple[str, Type[FlowPropagateStep[RecordType]], list[str]]
        ] = []

        # Store a mapping of step names to the method to run them
        # {
        #   "step1": StepMode.INCLUDE,
        #   "step2": StepMode.EXCLUDE,
        #   "step3": StepMode.DEBUG
        # }
        self.step_modes: dict[str, StepMode] = {}

        self.concrete_record_steps: list[
            tuple[str, FlowRecordStep[RecordType]]
        ] = []
        self.concrete_update_steps: list[
            tuple[str, FlowUpdateStep[RecordType], list[str]]
        ] = []
        self.concrete_propagate_steps: list[
            tuple[str, FlowPropagateStep[RecordType], list[str]]
        ] = []
        self.step_metadata: dict[str, object] = {}
        self._step_metadata_lock = Lock()

        self.logger = get_logger(self.name)
        self._log_lock = Lock()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Logging
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def silent(self: Self) -> None:
        """Make the flow suppress terminal output."""
        set_verbosity(False)

    def verbose(self: Self) -> None:
        """Enable terminal output, if it was previously disabled."""
        set_verbosity(True)

    def logfile(self: Self, file_path: str) -> None:
        """Add a logfile path, to output logs to."""
        if os.path.exists(file_path) and not os.path.isfile(file_path):
            raise Exception(
                f"Logfile path {file_path} already exists and isn't a file!"
            )

        add_logfile(self.logger, file_path)

    def flow_log(self: Self, msg: str) -> None:
        """Log a message from the flow.

        Args:
            msg (str): The message to log
        """
        with self._log_lock:
            self.logger.log(FLOW, msg)

    def flow_success(self: Self, msg: str) -> None:
        """Log a success message from the flow.

        Args:
            msg (str): The message to log
        """
        with self._log_lock:
            self.logger.log(SUCCESS, msg)

    def step_log(self: Self, step_name: str, msg: str) -> None:
        """Log a message from a step.

        Args:
            step_name (str): The step that's logging
            msg (str): The message to log
        """
        with self._log_lock:
            self.logger.log(STEP, f"[{step_name}] {msg}")

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Step Metadata
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def set_metadata(self: Self, name: str, value: object) -> None:
        """Set global metadata for the flow from a step.

        Args:
            self (Self): The flow to set metadata for
            name (str): The name of the metadata
            value (object): The value for the metadata
        """
        with self._step_metadata_lock:
            self.step_metadata[name] = value

    def get_metadata(self: Self, name: str) -> object:
        """Get global metadata from the flow for a step.

        Args:
            self (Self): The flow to set metadata for
            name (str): The name of the metadata

        Returns:
            object: The value of the metadata
        """
        with self._step_metadata_lock:
            if name in self.step_metadata:
                return self.step_metadata[name]
            else:
                return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Adding Steps
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def step_names(self: Self) -> list[str]:
        """Get the names of all the steps in the flow.

        Args:
            self (Self): The flow to get the step names for

        Returns:
            list[str]: The names of all the steps in the flow
        """
        record_names = [name for name, _ in self.record_steps]
        update_names = [name for name, _, _ in self.update_steps]
        propagate_names = [name for name, _, _ in self.propagate_steps]
        return record_names + update_names + propagate_names

    def step_exists(self: Self, step_name: str) -> bool:
        """Determine whether a step with the given name already exists.

        Args:
            step_name (str): The step's name

        Returns:
            bool: Whether a step with the name already exists
        """
        return any(
            step_name == name
            for name in (self.step_names() + [self.record_storer_name])
        )

    def add_record_step(
        self: Self, name: str, step: Type[FlowRecordStep[RecordType]]
    ) -> None:
        """Add a record step to the flow.

        Args:
            name (str): The name of the record step
            step (Type[FlowRecordStep[RecordType]]): The type of the record
              step

        Raises:
            Exception: Raised if a step with the name already exists
        """
        if name in self.step_names():
            raise Exception(f"{name} already exists as a step!")
        self.record_steps.append((name, step))

    def add_update_step(
        self: Self,
        name: str,
        step: Type[FlowUpdateStep[RecordType]],
        depends_on: list[str] = [],
    ) -> None:
        """Add an update step to the flow.

        Args:
            name (str): The name of the record step
            step (Type[FlowRecordStep[RecordType]]): The type of the record
              step
            depends_on (list[str]): Other steps that this one should run after

        Raises:
            Exception: Raised if a step with the name already exists, or if the
              step depends on other steps that don't exist or are the wrong
              type
        """
        curr_step_names = self.step_names()
        curr_update_step_names = [name for name, _, _ in self.update_steps]

        if name in curr_step_names:
            raise Exception(f"{name} already exists as a step!")
        for dependency in depends_on:
            if dependency not in curr_step_names:
                raise Exception(
                    f"Dependency {dependency} doesn't exist as a step!"
                )
            if dependency not in curr_update_step_names:
                raise Exception(
                    f"Dependency {dependency} isn't an update step!"
                )

        self.update_steps.append((name, step, depends_on))

    def add_propagate_step(
        self: Self,
        name: str,
        step: Type[FlowPropagateStep[RecordType]],
        depends_on: list[str] = [],
    ) -> None:
        """Add a propagate step to the flow.

        Args:
            name (str): The name of the record step
            step (Type[FlowRecordStep[RecordType]]): The type of the record
              step
            depends_on (list[str]): Other steps that this one should run after

        Raises:
            Exception: Raised if a step with the name already exists, or if the
              step depends on other steps that don't exist or are the wrong
              type
        """
        curr_step_names = self.step_names()
        curr_propagate_step_names = [
            name for name, _, _ in self.propagate_steps
        ]

        if name in curr_step_names:
            raise Exception(f"{name} already exists as a step!")
        for dependency in depends_on:
            if dependency not in curr_step_names:
                raise Exception(
                    f"Dependency {dependency} doesn't exist as a step!"
                )
            if dependency not in curr_propagate_step_names:
                raise Exception(
                    f"Dependency {dependency} isn't a propagate step!"
                )

        self.propagate_steps.append((name, step, depends_on))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Configuring
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def describe_config(self: Self) -> dict[str, str | dict[str, str]]:
        """Return a dictionary describing the flow and all steps.

        Args:
            self (Self): The flow to describe

        Returns:
            dict[str, str | dict[str, str]]: A mapping of configurations to
              descriptions, such that they could be taken in as a YAML file if
              used with the indicated types.
        """
        config_descriptions: dict[str, str | dict[str, str]] = {
            x[0]: f"({x[1].__name__}) {x[2]}" for x in flow_config_types
        }
        config_descriptions["_description"] = self.description

        # Include mode configurations for our record storer
        config_descriptions[f"{self.record_storer_name}-mode"] = (
            f"(str) The mode to run {self.record_storer_name} in "
            f"(either '{str(StepMode.INCLUDE)}' or "
            f"'{str(StepMode.DEBUG)}')"
        )

        # Include mode configurations for all added steps
        for step_name in self.step_names():
            config_descriptions[f"{step_name}-mode"] = (
                f"(str) The mode to run {step_name} in "
                f"(either '{str(StepMode.INCLUDE)}', "
                f"'{str(StepMode.EXCLUDE)}', or '{str(StepMode.DEBUG)}')"
            )

        # Include configurations for our record storer
        config_descriptions[self.record_storer_name] = (
            self.record_storer_type.describe_config()
        )

        # Include configurations for all of our steps
        for name, record_step_type in self.record_steps:
            config_descriptions[name] = record_step_type.describe_config()
        for name, update_step_type, _ in self.update_steps:
            config_descriptions[name] = update_step_type.describe_config()
        for name, propagate_step_type, _ in self.propagate_steps:
            config_descriptions[name] = propagate_step_type.describe_config()

        return config_descriptions

    def config(self: Self, config_dict: dict[str, Any]) -> None:
        """Configure the flow and its steps.

        Args:
            self (Self): The flow to configure
            config_dict (dict[str, Any]): The configurations for the flow
        """
        # First, check the type of the dictionary
        for value in config_dict.values():
            if isinstance(value, dict):
                for subvalue in value:
                    if not isinstance(subvalue, ValidConfigTypes):
                        raise Exception(
                            f"Illegal type {type(subvalue)} in "
                            f"configurations ({subvalue})"
                        )
            else:
                if not isinstance(value, ValidConfigTypes):
                    raise Exception(
                        f"Illegal type {type(subvalue)} in "
                        f"configurations ({subvalue})"
                    )

        # We can now interpret the configuration dictionary as the correct type
        config_dict = cast(
            dict[str, ValidConfigTypes | dict[str, ValidConfigTypes]],
            config_dict,
        )

        # Use literals to assign configurations to the flow, to take advantage
        # of the TypedDict
        if "num_threads" in config_dict:
            if isinstance(config_dict["num_threads"], int):
                self.configs["num_threads"] = config_dict["num_threads"]
            else:
                raise Exception("Configuration 'num_threads' isn't an int")
        else:
            raise Exception(
                "Configuration 'num_threads' isn't in configuration"
            )

        # Get whether our record storer is enabled
        if f"{self.record_storer_name}-mode" in config_dict:
            self.step_modes[self.record_storer_name] = StepMode(
                str(config_dict[f"{self.record_storer_name}-mode"])
            )
            if self.step_modes[self.record_storer_name] == StepMode.EXCLUDE:
                raise Exception("Can't exclude a record storer!")
        else:
            Exception(
                f"Configuration {self.record_storer_name}-mode isn't "
                "in configuration"
            )

        # Get whether each step is enabled
        for step_name in self.step_names():
            if f"{step_name}-mode" in config_dict:
                self.step_modes[step_name] = StepMode(
                    str(config_dict[f"{step_name}-mode"])
                )
            else:
                raise Exception(
                    f"Configuration {step_name}-mode isn't in configuration"
                )

        # Configure our record storer
        if self.record_storer_name in config_dict:
            if isinstance(config_dict[self.record_storer_name], dict):
                storer_config_dict = cast(
                    dict[str, ValidConfigTypes],
                    config_dict[self.record_storer_name],
                )
                storer_config_dict = {
                    x: y
                    for x, y in storer_config_dict.items()
                    if not x.startswith("_")
                }
                self.record_storer = self.record_storer_type(storer_config_dict)
            else:
                raise Exception(
                    f"Configuration '{self.record_storer_name}' isn't "
                    "a dictionary"
                )
        else:
            raise Exception(
                f"Configuration '{self.record_storer_name}' isn't "
                "in configuration"
            )

        # Configure/instantiate our steps
        for name, record_step_type in self.record_steps:
            if name in config_dict:
                if isinstance(config_dict[name], dict):
                    step_config_dict = cast(
                        dict[str, ValidConfigTypes],
                        config_dict[name],
                    )
                    step_config_dict = {
                        x: y
                        for x, y in step_config_dict.items()
                        if not x.startswith("_")
                    }
                    self.concrete_record_steps.append(
                        (name, record_step_type(step_config_dict))
                    )
                else:
                    raise Exception(
                        f"Configuration '{name}' isn't " "a dictionary"
                    )
            else:
                raise Exception(
                    f"Configuration '{name}' isn't " "in configuration"
                )
        for name, update_step_type, dependencies in self.update_steps:
            if name in config_dict:
                if isinstance(config_dict[name], dict):
                    step_config_dict = cast(
                        dict[str, ValidConfigTypes],
                        config_dict[name],
                    )
                    step_config_dict = {
                        x: y
                        for x, y in step_config_dict.items()
                        if not x.startswith("_")
                    }
                    self.concrete_update_steps.append(
                        (name, update_step_type(step_config_dict), dependencies)
                    )
                else:
                    raise Exception(
                        f"Configuration '{name}' isn't " "a dictionary"
                    )
            else:
                raise Exception(
                    f"Configuration '{name}' isn't " "in configuration"
                )
        for name, propagate_step_type, dependencies in self.propagate_steps:
            if name in config_dict:
                if isinstance(config_dict[name], dict):
                    step_config_dict = cast(
                        dict[str, ValidConfigTypes],
                        config_dict[name],
                    )
                    step_config_dict = {
                        x: y
                        for x, y in step_config_dict.items()
                        if not x.startswith("_")
                    }
                    self.concrete_propagate_steps.append(
                        (
                            name,
                            propagate_step_type(step_config_dict),
                            dependencies,
                        )
                    )
                else:
                    raise Exception(
                        f"Configuration '{name}' isn't " "a dictionary"
                    )
            else:
                raise Exception(
                    f"Configuration '{name}' isn't " "in configuration"
                )
        self.configured = True

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # Running
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _get_records(self: Self) -> list[RecordType]:
        """Get the records from the record storer.

        Args:
            self (Self): The flow to get records for

        Returns:
            list[RecordType]: The retrieved records
        """

        def log(msg: str) -> None:
            """Log a message from our record storer.

            Args:
                msg (str): The message to log
            """
            self.step_log(self.record_storer_name, msg)

        if self.record_storer is None:
            raise Exception("Flow isn't configured!")
        return self.record_storer.get_records(
            log,
            debug=(self.step_modes[self.record_storer_name] == StepMode.DEBUG),
        )

    def _set_records(self: Self, records: list[RecordType]) -> None:
        """Set the records using the record storer.

        Args:
            self (Self): The flow with the records.
            records (list[RecordType]): The records to store
        """

        def log(msg: str) -> None:
            """Log a message from our record storer.

            Args:
                msg (str): The message to log
            """
            self.step_log(self.record_storer_name, msg)

        if self.record_storer is None:
            raise Exception("Flow isn't configured!")
        self.record_storer.set_records(
            records,
            log,
            debug=(self.step_modes[self.record_storer_name] == StepMode.DEBUG),
        )

    def _run_record_steps(
        self: Self, records: list[RecordType]
    ) -> list[RecordType]:
        """Run our record steps over the list of records.

        Args:
            self (Self): The current flow
            records (list[RecordType]): The current list of records

        Returns:
            list[RecordType]: The updated list of records
        """
        enabled_record_steps = [
            step
            for step in self.concrete_record_steps
            if self.step_modes[step[0]] != StepMode.EXCLUDE
        ]

        for record_step in enabled_record_steps:
            name = record_step[0]
            step = record_step[1]

            def log(msg: str) -> None:
                """Log a message from our record step.

                Args:
                    msg (str): The message to log
                """
                self.step_log(name, msg)

            records = step.new_records(
                records,
                log,
                self.get_metadata,
                self.set_metadata,
                debug=(self.step_modes[name] == StepMode.DEBUG),
            )
        return records

    def _run_update_steps(self: Self, records: list[RecordType]) -> None:
        """Run our update steps over the list of records.

        Args:
            self (Self): The current flow
            records (list[RecordType]): The list of records to update
        """
        work_queue: list[Optional[tuple[str, FlowUpdateStep[RecordType]]]] = []
        work_queue_lock = Lock()

        completed_steps: list[str] = []
        completed_steps_lock = Lock()

        def add_work(
            new_work: Optional[tuple[str, FlowUpdateStep[RecordType]]]
        ) -> None:
            """Add new work to the work queue.

            Args:
                new_work (Optional[tuple[str, FlowUpdateStep[RecordType]]]):
                  The new work to send to the workers
            """
            with work_queue_lock:
                work_queue.append(new_work)

        # Use lock striping to protect records
        zipped_records = list(
            zip(records, [Lock() for _ in range(len(records))])
        )

        def worker(worker_name: str) -> None:
            """Run work from the work queue until told to stop by a 'None'.

            Args:
                worker_name (str): The name of the worker
            """
            while True:
                got_data = False
                while not got_data:
                    with work_queue_lock:
                        if len(work_queue) > 0:
                            new_work = work_queue.pop(0)
                            got_data = True
                    if not got_data:
                        time.sleep(3)

                # Use None as a sentinel value, since PEP 661 isn't
                # approved yet
                if new_work is None:
                    return

                # Otherwise, run the step
                name = new_work[0]
                step = new_work[1]

                def log(msg: str) -> None:
                    """Log a message from our update step.

                    Args:
                        msg (str): The message to log
                    """
                    self.step_log(name, msg)

                self.flow_log(f"Running {name} on {worker_name}")
                step.update_records(
                    zipped_records,
                    log,
                    self.get_metadata,
                    self.set_metadata,
                    debug=(self.step_modes[name] == StepMode.DEBUG),
                )
                with completed_steps_lock:
                    completed_steps.append(name)

        # Get our steps to run, updating dependencies to only reflect enabled
        # steps
        enabled_update_steps = [
            step
            for step in self.concrete_update_steps
            if self.step_modes[step[0]] != StepMode.EXCLUDE
        ]
        enabled_update_step_names = [step[0] for step in enabled_update_steps]

        def new_deps(curr_deps: list[str]) -> list[str]:
            """Update dependencies based on enabled steps.

            Args:
                curr_deps (list[str]): The current dependencies

            Returns:
                list[str]: The updated dependencies
            """
            return [
                dep for dep in curr_deps if dep in enabled_update_step_names
            ]

        enabled_update_steps = [
            (name, step, new_deps(deps))
            for (name, step, deps) in enabled_update_steps
        ]

        # Start a pool of workers
        if self.configs["num_threads"] < 1:
            raise Exception(
                "Configuration 'num_threads' doesn't use any threads!"
            )
        worker_pool = [
            Thread(target=worker, args=[f"Worker {i}"])
            for i in range(self.configs["num_threads"])
        ]
        for worker_thread in worker_pool:
            worker_thread.start()

        # Progressively add work to the queue as other steps finish
        remaining_steps = enabled_update_steps
        while len(remaining_steps) > 0:
            new_remaining_steps: list[
                tuple[str, FlowUpdateStep[RecordType], list[str]]
            ] = []
            with completed_steps_lock:
                new_completed_steps = completed_steps
            for name, step, deps in remaining_steps:
                work_ready = all([dep in new_completed_steps for dep in deps])
                if work_ready:
                    add_work((name, step))
                else:
                    new_remaining_steps.append((name, step, deps))
            remaining_steps = new_remaining_steps
            time.sleep(3)

        # Close out all remaining threads
        for _ in range(self.configs["num_threads"]):
            add_work(None)
        for worker_thread in worker_pool:
            worker_thread.join()

        # Copy all records back over
        for i in range(len(records)):
            records[i] = zipped_records[i][0]

    def _run_propagate_steps(self: Self, records: list[RecordType]) -> None:
        """Run our propagate steps over the list of records.

        Args:
            self (Self): The current flow
            records (list[RecordType]): The list of records to update
        """
        work_queue: list[
            Optional[tuple[str, FlowPropagateStep[RecordType]]]
        ] = []
        work_queue_lock = Lock()

        completed_steps: list[str] = []
        completed_steps_lock = Lock()

        def add_work(
            new_work: Optional[tuple[str, FlowPropagateStep[RecordType]]]
        ) -> None:
            """Add new work to the work queue.

            Args:
                new_work (Optional[tuple[str, FlowUpdateStep[RecordType]]]):
                  The new work to send to the workers
            """
            with work_queue_lock:
                work_queue.append(new_work)

        # Use lock striping to protect records
        zipped_records = list(
            zip(records, [Lock() for _ in range(len(records))])
        )

        def worker(worker_name: str) -> None:
            """Run work from the work queue until told to stop by a 'None'.

            Args:
                worker_name (str): The name of the worker
            """
            while True:
                got_data = False
                while not got_data:
                    with work_queue_lock:
                        if len(work_queue) > 0:
                            new_work = work_queue.pop(0)
                            got_data = True
                    if not got_data:
                        time.sleep(3)

                # Use None as a sentinel value, since PEP 661 isn't
                # approved yet
                if new_work is None:
                    return

                # Otherwise, run the step
                name = new_work[0]
                step = new_work[1]

                def log(msg: str) -> None:
                    """Log a message from our propagate step.

                    Args:
                        msg (str): The message to log
                    """
                    self.step_log(name, msg)

                self.flow_log(f"Running {name} on {worker_name}")
                step.propagate_records(
                    zipped_records,
                    log,
                    self.get_metadata,
                    self.set_metadata,
                    debug=(self.step_modes[name] == StepMode.DEBUG),
                )
                with completed_steps_lock:
                    completed_steps.append(name)

        # Get our steps to run, updating dependencies to only reflect enabled
        # steps
        enabled_propagate_steps = [
            step
            for step in self.concrete_propagate_steps
            if self.step_modes[step[0]] != StepMode.EXCLUDE
        ]
        enabled_propagate_step_names = [
            step[0] for step in enabled_propagate_steps
        ]

        def new_deps(curr_deps: list[str]) -> list[str]:
            """Update dependencies based on enabled steps.

            Args:
                curr_deps (list[str]): The current dependencies

            Returns:
                list[str]: The updated dependencies
            """
            return [
                dep for dep in curr_deps if dep in enabled_propagate_step_names
            ]

        enabled_propagate_steps = [
            (name, step, new_deps(deps))
            for (name, step, deps) in enabled_propagate_steps
        ]

        # Start a pool of workers
        if self.configs["num_threads"] < 1:
            raise Exception(
                "Configuration 'num_threads' doesn't use any threads!"
            )
        worker_pool = [
            Thread(target=worker, args=[f"Worker {i}"])
            for i in range(self.configs["num_threads"])
        ]
        for worker_thread in worker_pool:
            worker_thread.start()

        # Progressively add work to the queue as other steps finish
        remaining_steps = enabled_propagate_steps
        while len(remaining_steps) > 0:
            new_remaining_steps: list[
                tuple[str, FlowPropagateStep[RecordType], list[str]]
            ] = []
            with completed_steps_lock:
                new_completed_steps = completed_steps
            for name, step, deps in remaining_steps:
                work_ready = all([dep in new_completed_steps for dep in deps])
                if work_ready:
                    add_work((name, step))
                else:
                    new_remaining_steps.append((name, step, deps))
            remaining_steps = new_remaining_steps
            time.sleep(3)

        # Close out all remaining threads
        for _ in range(self.configs["num_threads"]):
            add_work(None)
        for worker_thread in worker_pool:
            worker_thread.join()

        # Copy all records back over
        for i in range(len(records)):
            records[i] = zipped_records[i][0]

    def run(self: Self) -> None:
        """Run all of the steps, getting and storing the needed records.

        Args:
            self (Self): The flow to run
        """
        self.flow_log("==================================================")
        self.flow_log(self.name)
        self.flow_log("==================================================")
        self.flow_log(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        self.flow_log(f"Number of threads: {str(self.configs['num_threads'])}")

        self.flow_log(f"Getting records from {self.record_storer_name}")
        records = self._get_records()

        self.flow_log("")
        self.flow_log("--------------------------------------------------")
        self.flow_log("Running record steps...")
        self.flow_log("--------------------------------------------------")
        records = self._run_record_steps(records)

        self.flow_log("")
        self.flow_log("--------------------------------------------------")
        self.flow_log("Running update steps...")
        self.flow_log("--------------------------------------------------")
        self._run_update_steps(records)

        self.flow_log("")
        self.flow_log("--------------------------------------------------")
        self.flow_log("Running propagate steps...")
        self.flow_log("--------------------------------------------------")
        self._run_propagate_steps(records)

        self.flow_log("")
        self.flow_log(f"Storing records in {self.record_storer_name}")
        self._set_records(records)

        self.flow_success(
            "Flow finished successfully at "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
