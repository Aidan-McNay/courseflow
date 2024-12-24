"""An abstract base class for objects that can be stored in spreadsheets.

Author: Aidan McNay
Date: September 14th, 2024
"""

from abc import ABC, abstractmethod
from typing import Self, Type, TypeVar

# -----------------------------------------------------------------------------
# SpreadsheetRecord
# -----------------------------------------------------------------------------
# An object that can be represented as a list of strings

# Use a type variable to represent this class and all children

SpreadsheetRecordChild = TypeVar(
    "SpreadsheetRecordChild", bound="SpreadsheetRecord"
)


class SpreadsheetRecord(ABC):
    """A specific record type that can be represented in a spreadsheet.

    To achieve this, the object must be able to be expressed from and as
    a list of strings.
    """

    # Records must define their headers
    @property
    @abstractmethod
    def headers(self: Self) -> list[str]:
        """The headers for the given object."""
        return []

    # Must be able to represent itself as a list of strings
    @abstractmethod
    def to_strings(self: Self) -> list[str]:
        """Represent itself as a list of strings.

        The list should be the same length as its headers, with each element
        representing the data for the corresponding header.

        Args:
            self (Self): The object to represent as strings

        Returns:
            list[str]: The representation as strings
        """
        return []

    # Must be able to make itself from strings
    @classmethod
    @abstractmethod
    def from_strings(
        cls: Type[SpreadsheetRecordChild], header_mapping: dict[str, str]
    ) -> SpreadsheetRecordChild:
        """Construct itself from a mapping of strings.

        Args:
            header_mapping (dict[str, str]): A mapping of headers to the
              data under the header. Some headers may not be present, and
              the class must determine whether it can still be constructed.

        Returns:
            Self: The constructed mapping
        """
