"""A RecordStorer for getting and storing records in Google Sheets.

Author: Aidan McNay
Date: September 16th, 2024
"""

from datetime import datetime
from typing import Callable, get_args, Self, TypeVar

from google_steps import _sheets
from flow.record_storer import RecordStorer
from records.spreadsheet_record import SpreadsheetRecord
from utils.api_call import retry_call

# -----------------------------------------------------------------------------
# SpreadsheetStorer
# -----------------------------------------------------------------------------

# Our storer can operate on any SpreadsheetRecord
RecordType = TypeVar("RecordType", bound=SpreadsheetRecord)


class SpreadsheetStorer(RecordStorer[RecordType]):
    """An abstraction of getting and storing records in a Google Sheet."""

    description = (
        "A Python representation of a Google Sheet for "
        "getting and setting records"
    )

    config_types = [
        ("sheet_id", str, "The ID of the Google Sheet to access"),
        ("tab", str, "The tab to access for records"),
    ]

    def validate(self: Self) -> None:
        """Validate the configurations for the spreadsheet storer.

        Args:
            self (Self): The step to validate
        """
        # Make sure we can connect to the spreadsheet
        try:
            retry_call(_sheets.open_by_key, self.configs.sheet_id)
        except Exception:
            raise Exception(
                "Couldn't access spreadsheet - make sure it is "
                "shared to the service account"
            )

    def get_records(
        self: Self, logger: Callable[[str], None], debug: bool = False
    ) -> list[RecordType]:
        """Get the records from the spreadsheet.

        Args:
            logger (Callable[[str], None]): A logger for recording notable
              events
            debug (bool): Whether to run in debug mode. Defaults to False

        Returns:
            list[T]: The retrieved records
        """
        if debug:
            logger("Ignoring debug for SpreadsheetStorer")
        logger("Accessing spreadsheet...")
        sheet = retry_call(_sheets.open_by_key, self.configs.sheet_id)
        logger(f"Accessed spreadsheet '{sheet.title}'")

        if self.configs.tab in [
            worksheet.title for worksheet in retry_call(sheet.worksheets)
        ]:
            logger(f"Found worksheet '{self.configs.tab}'")
            worksheet = retry_call(sheet.worksheet, self.configs.tab)
        else:
            logger(f"Creating worksheet '{self.configs.tab}'")
            worksheet = retry_call(
                sheet.add_worksheet, title=self.configs.tab, rows=1, cols=1
            )

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # Get the records from the worksheet
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        data = retry_call(worksheet.get_all_values)

        try:
            last_updated = data[0][0]
            if last_updated != "Last Updated:":
                return []
            headers = data[1]
        except Exception:
            logger("Detecting blank worksheet {}; no records available")
            return []

        records = []

        # Hacky way to get the generic data type
        record_type = get_args(self.__orig_class__)[0]  # type: ignore

        for row in data[2:]:
            try:
                header_data_mapping = {
                    header: row[idx] for idx, header in enumerate(headers)
                }
                records.append(record_type.from_strings(header_data_mapping))
            except Exception:
                pass
        logger(f"Found {len(records)} records!")
        return records

    def set_records(
        self: Self,
        rec_list: list[RecordType],
        logger: Callable[[str], None],
        debug: bool = False,
    ) -> None:
        """Store the updated records in the Google Sheet.

        Args:
            rec_list (list[T]): The records to store
            logger (Callable[[str], None]): A logger for recording notable
              events
            debug (bool): Whether to run in debug mode. Defaults to False
        """
        # Hacky way to get the generic data type
        record_type = get_args(self.__orig_class__)[0]  # type: ignore

        cells = [["Last Updated:", datetime.now().strftime("%Y-%m-%d %H:%M")]]
        cells.append(record_type.headers)
        for record in rec_list:
            cells.append(record.to_strings())

        if debug:
            logger("DEBUG: Avoiding storing records")
        else:
            sheet = retry_call(_sheets.open_by_key, self.configs.sheet_id)
            worksheet = retry_call(sheet.worksheet, self.configs.tab)
            retry_call(worksheet.clear)
            retry_call(worksheet.update, cells)
            logger(
                f"Stored records in '{self.configs.tab}' tab of {sheet.title}"
            )
