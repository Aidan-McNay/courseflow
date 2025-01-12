# Record Steps

## Base Class

```{eval-rst}
All record steps must inherit from/implement the following base class
(with some repeated from :py:class:`~flow.flow_steps.FlowStep`)

.. autoclass:: flow.flow_steps.FlowRecordStep()

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

   .. automethod:: new_records
```

## Implementations

```{eval-rst}
.. autoclass:: canvas_steps.enrollment.AddEnrollment()

   This step gets the current enrollment from Canvas, and creates a new
   record for any student that there isn't a record for already.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   Sets metadata: :py:attr:`new_netids`
```

```{eval-rst}
.. autoclass:: google_steps.get_tag_records.GetTagRecords()

   This step assumes that a spreadsheet contains
   :py:class:`~records.student_record.StudentRecord`\ s (such as those
   made by :py:class:`~google_steps.spreadsheet_storer.SpreadsheetStorer`),
   and translates them to :py:class:`~records.tag_record.TagRecords`\ s
   (adding a non-tagged :py:class:`~records.tag_record.TagRecords` for 
   each non-empty personal and group repo entry).

   Supported record types: :py:class:`~records.tag_record.TagRecords`

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

```{eval-rst}
.. autoclass:: utils.basic_steps.BasicRecordStep()

   The record is chosen at random between 0 and 10 (inclusive).

   Supported record types: ``int``
```