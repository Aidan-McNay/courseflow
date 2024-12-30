# Record Storers

## Base Class

## Implementations

### SpreadsheetStorer

```{eval-rst}
.. autoclass:: google_steps.spreadsheet_storer.SpreadsheetStorer()
   :exclude-members: get_records, set_records, validate

   Test test, this is a test

   .. py:attribute:: configs.sheet_id
      :type: str

      The ID of the Google Sheet to access

   .. admonition:: Service Account access
      :class: note

      Make sure that your service account has access to the Google Sheet
      with this ID!

   .. py:attribute:: configs.tag
      :type: str

      The Google Sheet tab to access for records
```