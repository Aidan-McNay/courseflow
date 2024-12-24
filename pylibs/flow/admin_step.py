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
# AdminStep
# -----------------------------------------------------------------------------
# A base class for all future steps

ValidConfigTypes = int | bool | str | datetime

AdminStepChild = TypeVar("AdminStepChild", bound="AdminStep")


class AdminStep(ABC):
    """A base class representing an abstract step in our flow.

    Attributes:
     - description: (str) A high-level description of the step
     - config_types (list[tuple[str, str, Type]]): A list of (name, type,
         description) tuples describing the intended configurations for the
         step.
     - config_type: (Type) The type for our configurations. The type will be
         such that if the AdminStep is defined with

         config_types = [
           ("x", int,  "An integer"),
           ("y", bool, "A boolean" )
         ]

         then

         config_type.x : int
         config_type.y : bool
     - configs: (Optional[config_type]) The configurations for our step.
    """

    # Base classes must define their description and configuration types
    description = "Not Set"
    config_types: list[tuple[str, Type[ValidConfigTypes], str]] = [
        ("not-set", str, "A placeholder to indicate unset config types")
    ]

    @abstractmethod
    def validate(self: Self) -> None:
        """Validate the configurations for the step.

        Args:
            self (Self): The step to validate
        """
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
    def describe_config(cls: Type[AdminStepChild]) -> dict[str, str]:
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
# AdminRecordStep
# -----------------------------------------------------------------------------
# A flow step for adding new records.

RecordType = TypeVar("RecordType")


class AdminRecordStep(AdminStep, Generic[RecordType]):
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
# AdminUpdateStep
# -----------------------------------------------------------------------------
# A flow step for updating existing records


class AdminUpdateStep(AdminStep, Generic[RecordType]):
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
            records (list[RecordType]): The list of records to manipulate
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
# AdminPropagateStep
# -----------------------------------------------------------------------------
# A flow step for making external changes based on our records


class AdminPropagateStep(AdminStep, Generic[RecordType]):
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
        """Update our records with any new information.

        Args:
            records (list[RecordType]): The list of records to manipulate
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
