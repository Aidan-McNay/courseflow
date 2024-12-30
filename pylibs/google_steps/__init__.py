"""Set common variables and drivers for the Google API.

Required environment variables:
 - GOOGLE_API_JSON: The path to your Google service account credential
                    JSON file
"""

import gspread
import os
from typing import cast

# Initialize our main service account object
#  - For documentation generation, use a dummy object, and pretend it's
#    the correct type for linting
if "AUTODOC_GEN" in os.environ:
    _sheets = cast(gspread.client.Client, object())
else:
    _sheets = gspread.auth.service_account(
        filename=os.environ["GOOGLE_API_JSON"]
    )
