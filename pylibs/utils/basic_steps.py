"""Basic steps to understand the structure of flows.

Author: Aidan McNay
Date: December 29th, 2024
"""

import os
from pathlib import Path
import random
from threading import Lock
from typing import Any, Callable, Self

from flow.flow_steps import FlowRecordStep, FlowUpdateStep, FlowPropagateStep
from flow.record_storer import RecordStorer

# -----------------------------------------------------------------------------
# BasicRecordStorer
# -----------------------------------------------------------------------------
# A record storer which stores integer records in a file


class BasicRecordStorer(RecordStorer[int]):
    """A basic record storer that stores integers in a file."""

    description = "A basic record storer that stores integers in a file."
    config_types = [("file_path", str, "The path to a file to store records")]

    def validate(self: "BasicRecordStorer") -> None:
        """Validate the configurations for the step.

        Args:
            self (BasicRecordStorer): The step to validate
        """
        if not os.path.isfile(self.configs.file_path):
            if os.path.exists(self.configs.file_path):
                raise Exception("Path exists, but isn't file!")
            Path(self.configs.file_path).touch()
        else:
            # Make sure we can interpret the path as a list of integers
            with open(self.configs.file_path, "r") as f:
                _ = [int(x) for x in f.readlines()]

    def get_records(
        self: "BasicRecordStorer",
        logger: Callable[[str], None],
        debug: bool = False,
    ) -> list[int]:
        """Get the records from the file.

        Args:
            self (BasicRecordStorer): The record storer to get records with
            logger (Callable[[str], None]): A logger for recording notable
              events
            debug (bool): Whether to run in debug mode. Defaults to False

        Returns:
            list[T]: The retrieved records
        """
        with open(self.configs.file_path, "r") as f:
            records = [int(x) for x in f.readlines()]
        if debug:
            logger(
                f"DEBUG: Found {len(records)} records in "
                f"{self.configs.file_path}"
            )
        return records

    def set_records(
        self: Self,
        rec_list: list[int],
        logger: Callable[[str], None],
        debug: bool = False,
    ) -> None:
        """Store the updated records in the file.

        Args:
            self (BasicRecordStorer): The record storer to store records with
            rec_list (list[int]): The records to store
            logger (Callable[[str], None]): A logger for recording notable
              events
            debug (bool): Whether to run in debug mode. Defaults to False
        """
        if debug:
            logger(
                f"DEBUG: Writing {len(rec_list)} records to "
                f"{self.configs.file_path}"
            )
        with open(self.configs.file_path, "w") as f:
            f.writelines("\n".join(str(x) for x in rec_list))


# -----------------------------------------------------------------------------
# BasicRecordStep
# -----------------------------------------------------------------------------
# A record step which adds a new integer record


class BasicRecordStep(FlowRecordStep[int]):
    """A basic flow record step to add a new record."""

    description = "A basic flow record step to add a (changing) new record."
    config_types = []

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        return

    def new_records(
        self: Self,
        curr_records: list[int],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> list[int]:
        """Add a new record to the list.

        Args:
            self (Self): The current step
            curr_records (list[int]): The current list of records
            logger (Callable[[str], None]): A function to log data
            get_metadata (Callable[[str], Any]): A function to get flow
              metadata
            set_metadata (Callable[[str, Any], None]): A function to get
              flow metadata
            debug (bool, optional): Whether to run in debug. Defaults to
              False.

        Returns:
            list[int]: The new list of records
        """
        new_record = random.randint(0, 10)
        if debug:
            logger(f"DEBUG: Adding new record: {str(new_record)}")
        curr_records.append(new_record)
        return curr_records


# -----------------------------------------------------------------------------
# BasicUpdateStep
# -----------------------------------------------------------------------------
# A record step which adds an increment to each integer record


class BasicUpdateStep(FlowUpdateStep[int]):
    """A basic flow update step to increment records."""

    description = "A basic flow update step to increment all records"
    config_types = [("increment", int, "The amount to increment by")]

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        if self.configs.increment < 0:
            raise Exception("The increment must be positive!")

    def update_records(
        self: Self,
        records: list[tuple[int, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Increment all records by the configured amount.

        Args:
            self (Self): The current step
            curr_records (list[tuple[int, Lock]]): The current list of records
            logger (Callable[[str], None]): A function to log data
            get_metadata (Callable[[str], Any]): A function to get flow
              metadata
            set_metadata (Callable[[str, Any], None]): A function to get
              flow metadata
            debug (bool, optional): Whether to run in debug. Defaults to
              False.

        Returns:
            list[int]: The new list of records
        """
        for idx, (record, lock) in enumerate(records):
            with lock:
                new_record = record + self.configs.increment
                if debug:
                    logger(f"DEBUG: Incrementing {record} -> {new_record}")
                records[idx] = (new_record, lock)


# -----------------------------------------------------------------------------
# BasicPropagateStep
# -----------------------------------------------------------------------------
# A record step which logs the sum of all integer records


class BasicPropagateStep(FlowPropagateStep[int]):
    """A basic flow propagate step to log the sum of all records."""

    description = "A basic flow propagate step to log the sum of all records"
    config_types = []

    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
        return

    def propagate_records(
        self: Self,
        records: list[tuple[int, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Log the sum of all records.

        Args:
            self (Self): The current step
            curr_records (list[tuple[int, Lock]]): The current list of records
            logger (Callable[[str], None]): A function to log data
            get_metadata (Callable[[str], Any]): A function to get flow
              metadata
            set_metadata (Callable[[str, Any], None]): A function to get
              flow metadata
            debug (bool, optional): Whether to run in debug. Defaults to
              False.

        Returns:
            list[int]: The new list of records
        """
        sum = 0
        for record, _ in records:
            if debug:
                logger(f"DEBUG: Adding {record} to sum...")
            sum += record
        logger(f"Record sum: {sum}")
