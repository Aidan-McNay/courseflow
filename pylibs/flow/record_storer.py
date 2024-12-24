"""An interface for objects that enable the retrieval and storage of records.

Author: Aidan McNay
Date: September 14th, 2024
"""

from abc import abstractmethod
from typing import Callable, Generic, Self, TypeVar

from flow.admin_step import AdminStep

# -----------------------------------------------------------------------------
# RecordStorer
# -----------------------------------------------------------------------------
# A base class for getting and storing records


RecordType = TypeVar("RecordType")


# Inherit from AdminStep to make sure that a RecordStorer can be configured
class RecordStorer(AdminStep, Generic[RecordType]):
    """An abstract interface for retrieving and storing records."""

    @abstractmethod
    def get_records(
        self: Self, logger: Callable[[str], None], debug: bool = False
    ) -> list[RecordType]:
        """Get the records from wherever they're stored.

        Args:
            logger (Callable[[str], None]): A logger for recording notable
              events
            debug (bool): Whether to run in debug mode. Defaults to False

        Returns:
            list[T]: The retrieved records
        """
        return []

    @abstractmethod
    def set_records(
        self: Self,
        rec_list: list[RecordType],
        logger: Callable[[str], None],
        debug: bool = False,
    ) -> None:
        """Store the updated records.

        Args:
            rec_list (list[T]): The records to store
            logger (Callable[[str], None]): A logger for recording notable
              events
            debug (bool): Whether to run in debug mode. Defaults to False
        """
        return
