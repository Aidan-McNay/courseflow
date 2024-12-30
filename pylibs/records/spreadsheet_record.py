"""An abstract base class for objects that can be stored in spreadsheets.

Author: Aidan McNay
Date: September 14th, 2024
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar

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
    def headers(self: "SpreadsheetRecord") -> list[str]:
        """The headers to use for the given object.

        These should be sufficient to represent all data in an object
        instance, and be of the same order as the data in the string
        representation.
        """
        return []

    # Must be able to represent itself as a list of strings
    @abstractmethod
    def to_strings(self: "SpreadsheetRecord") -> list[str]:
        """Represent itself as a list of strings.

        The list should be the same length as its headers, with each element
        representing the data for the corresponding header.

        Returns:
            list[str]: A representation of the instance as strings
        """
        return []

    # Must be able to make itself from strings
    @classmethod
    @abstractmethod
    def from_strings(
        cls: Type[SpreadsheetRecordChild], header_mapping: dict[str, str]
    ) -> "SpreadsheetRecord":
        """Construct itself from a mapping of strings.

        Args:
            header_mapping (dict[str, str]): A mapping of headers to the
              data under the header. Some headers may not be present, and
              the class must determine whether it can still be constructed.

        Returns:
            SpreadsheetRecord: An instance of the class constructed
              from the provided data
        """
