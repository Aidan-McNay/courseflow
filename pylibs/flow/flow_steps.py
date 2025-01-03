"""Abstract base classes for the various steps used in our flow.

Author: Aidan McNay
Date: September 14th, 2024
"""

from abc import ABC, abstractmethod
from dataclasses import make_dataclass
from datetime import datetime
from threading import Lock
from typing import Any, Callable, final, Generic, Self, Type, TypeVar

# -----------------------------------------------------------------------------
# FlowStep
# -----------------------------------------------------------------------------
# A base class for all future steps

ValidConfigTypes = int | bool | str | datetime

FlowStepChild = TypeVar("FlowStepChild", bound="FlowStep")


class FlowStep(ABC):
    """A base class representing an abstract step in our flow.

    Attributes:
     - description (str): A high-level description of the step
     - config_types (list[tuple[str, Type[ValidConfigTypes], str]]):
         The types for our configurations. Instances of the object will
         have an attribute ``configs`` that has each listed attribute of
         the defined name and type
     - configs (See ``config_types``): The configurations for our step.
         See ``config_types``
    """

    # Base classes must define their description and configuration types
    description = "Not Set"
    config_types: list[tuple[str, Type[ValidConfigTypes], str]] = [
        ("not-set", str, "A placeholder to indicate unset config types")
    ]

    @abstractmethod
    def validate(self: Self) -> None:
        """Validate the configurations for the step."""
        return

    @final
    def __init__(self: Self, configs: dict[str, Any]) -> None:
        """Create a new admin step.

        Here, we also check that the configurations are the correct type.

        Args:
            configs (dict[str, Any]): The candidate configurations for the
              step

        Raises:
            TypeError: Raised if the configurations aren't the correct type
        """
        if self.description == "Not Set":
            raise Exception(
                f"{self.__class__.__name__} didn't set a description!"
            )
        if (len(self.config_types) > 0) and (
            self.config_types[0][0] == "not-set"
        ):
            raise Exception(
                f"{self.__class__.__name__} didn't set configuration types!"
            )

        self.config_type = make_dataclass(
            f"{self.__class__.__name__}Configs",
            [(x[0], x[1]) for x in self.config_types],
        )

        for name, type, _ in self.config_types:
            if name not in configs:
                raise TypeError(
                    f"{name} not present in configuration "
                    f"for {self.__class__.__name__}"
                )
            if not isinstance(configs[name], type):
                raise TypeError(
                    f"{name} configuration not of type {type.__name__} "
                    f"for {self.__class__.__name__}"
                )
        self.configs = self.config_type(**configs)
        self.validate()

    @classmethod
    def describe_config(cls: Type[FlowStepChild]) -> dict[str, str]:
        """Return a mapping of configurations to their descriptions.

        Returns:
            dict[str, str]: A mapping of configuration names to a high-level
              description
        """
        config_descriptions = {
            x[0]: f"({x[1].__name__}) {x[2]}" for x in cls.config_types
        }
        config_descriptions["_description"] = cls.description
        return config_descriptions


# -----------------------------------------------------------------------------
# FlowRecordStep
# -----------------------------------------------------------------------------
# A flow step for adding new records.

RecordType = TypeVar("RecordType")


class FlowRecordStep(FlowStep, Generic[RecordType]):
    """A flow step to update the overall list of records."""

    @abstractmethod
    def new_records(
        self: Self,
        curr_records: list[RecordType],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> list[RecordType]:
        """Add any new records to the list of records.

        Args:
            curr_records (list[RecordType]): The current list of records
            logger (Callable[[str], None]): A function to log any notable
              events
            get_metadata (Callable[[str], Any],): A function to retrieve global
              metadata previously set in the flow
            set_metadata (Callable[[str, Any], None]): A function to set
              global metadata within the flow
            debug (bool, optional): Whether we are in "debug" mode. In debug
              mode, no external state should be modified, and we are free to
              inject dummy information. Defaults to False.

        Returns:
            list[RecordType]: The possibly augmented list of records
        """
        return []


# -----------------------------------------------------------------------------
# FlowUpdateStep
# -----------------------------------------------------------------------------
# A flow step for updating existing records


class FlowUpdateStep(FlowStep, Generic[RecordType]):
    """A flow step to update the overall list of records."""

    @abstractmethod
    def update_records(
        self: Self,
        records: list[tuple[RecordType, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Update our records with any new information.

        Args:
            records (list[tuple[RecordType, Lock]]): The list of records
              to manipulate
            logger (Callable[[str], None]): A function to log any notable
              events
            get_metadata (Callable[[str], Any],): A function to retrieve global
              metadata previously set in the flow
            set_metadata (Callable[[str, Any], None]): A function to set
              global metadata within the flow
            debug (bool, optional): Whether we are in "debug" mode. In debug
              mode, no external state should be modified, and we are free to
              inject dummy information. Defaults to False.
        """
        return


# -----------------------------------------------------------------------------
# FlowPropagateStep
# -----------------------------------------------------------------------------
# A flow step for making external changes based on our records


class FlowPropagateStep(FlowStep, Generic[RecordType]):
    """A flow step to make external changes based on our records."""

    @abstractmethod
    def propagate_records(
        self: Self,
        records: list[tuple[RecordType, Lock]],
        logger: Callable[[str], None],
        get_metadata: Callable[[str], Any],
        set_metadata: Callable[[str, Any], None],
        debug: bool = False,
    ) -> None:
        """Propagate our records to update any external entities.

        Args:
            records (list[tuple[RecordType, Lock]]): The list of records
              to manipulate
            logger (Callable[[str], None]): A function to log any notable
              events
            get_metadata (Callable[[str], Any],): A function to retrieve global
              metadata previously set in the flow
            set_metadata (Callable[[str, Any], None]): A function to set
              global metadata within the flow
            debug (bool, optional): Whether we are in "debug" mode. In debug
              mode, no external state should be modified, and we are free to
              inject dummy information. Defaults to False.
        """
        return
