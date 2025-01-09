# Record Storers

## Base Class

```{eval-rst}
All record storers must inherit from/implement the following base class
(with some repeated from :py:class:`~flow.flow_steps.FlowStep`)

.. autoclass:: flow.record_storer.RecordStorer()

   Parent Class: :py:class:`~flow.flow_steps.FlowStep`

   .. py:property:: description
      :abstractmethod:
      :classmethod:
      :type: str

      A high-level description of the step

   .. py:property:: config_types
      :abstractmethod:
      :classmethod:
      :type: list[tuple[str, Type[ValidConfigTypes], str]]

      The types of the configurations for the step. Each tuple in the list
      should include the name, type, and description of a configuration
      (respectively). See :py:class:`~flow.flow_steps.FlowStep`

   .. py:method:: validate() -> None
      :abstractmethod:

      This function should inspect the object's ``configs`` attribute, and
      perform any static validation possible.

   .. automethod:: get_records

   .. automethod:: set_records
```

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

```{eval-rst}
.. autoclass:: google_steps.spreadsheet_storer.SpreadsheetStorer()

   If multiple flows are accessing the spreadsheet at the same time, there
   is the possibility of data being miscommunicated if one flow reads at
   the same time that another clears the spreadsheet while updating.
   To address this, a global lock is implemented using POSIX file locks
   and ``fcntl.lockf`` to ensure proper synchronization between flows
   (running on the same system, which is assumed).

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