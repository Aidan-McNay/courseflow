# Record Storers

## Base Class

## Implementations

```{eval-rst}
.. autoclass:: utils.basic_steps.BasicRecordStorer()

   Supported record types: ``int``

   .. py:attribute:: configs.file_path
      :type: str

      The path to a file to source and store integers from
   
   .. automethod:: validate

      Specifically, we make sure that the supplied path doesn't represent
      a pre-existing non-file object, and that we have permissions to
      read from it
```

### SpreadsheetStorer

```{eval-rst}
.. autoclass:: google_steps.spreadsheet_storer.SpreadsheetStorer()

   Supported record types: :py:class:`~records.spreadsheet_record.SpreadsheetRecord`

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

   .. automethod:: validate

      Specifically, we make sure that the service account can access the
      specified Google Sheet
```