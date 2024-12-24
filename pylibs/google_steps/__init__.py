"""Set common variables and drivers for the Google API.

Required environment variables:
 - GOOGLE_API_JSON: The path to your Google service account credential
                    JSON file
"""

import gspread
import os

# Initialize our main service account object
#  - Have mypy ignore, as it isn't explicitly exported, but mentioned in the
#    documentation
_sheets = gspread.auth.service_account(filename=os.environ["GOOGLE_API_JSON"])
