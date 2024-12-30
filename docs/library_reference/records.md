# Records

Records used in flows can be any types; however, steps may often only work
with a specific subset of types. It is therefore useful to define base
classes, such that steps will work with any type that implements the base
class.

## Base Classes

```{eval-rst}
.. autoclass:: records.spreadsheet_record.SpreadsheetRecord

   Child classes must accordingly identify the headers that should be used
   in a spreadsheet that contains them:

   .. autoattribute:: headers

   Additionally, child classes must implement the following two methods to
   enable translation to and from a spreadsheet representation:

   .. automethod:: to_strings

   .. automethod:: from_strings
```

## Implementations

Currently, the following two classes are used by the majority of
implemented steps to achieve the necessary functionality:

```{eval-rst}
.. autoclass:: records.student_record.StudentRecord
   :show-inheritance:

   .. autoattribute:: headers

   .. automethod:: to_strings

   .. automethod:: from_strings
```

```{eval-rst}
.. autoclass:: records.tag_record.TagRecords
   :show-inheritance:

   .. admonition:: Using :py:class:`~records.tag_record.TagRecords`
      :class: note

      :py:class:`~records.tag_record.TagRecords` are meant to be
      inherited from in order to use; this is to allow flexibility with
      how many submissions/labs they represent, while maintaining string
      typing. When creating a child class, users must:

      * Override the ``labs`` class attribute to represent all necessary
        labs to tag
      * Override the ``headers`` attribute to accurately reflect the new
        headers needed to represent the class in a spreadsheet

      An example is provided below, where the resulting ``MyTagRecords``
      represents tags for two lab submissions (using 
      :py:func:`get_tag_headers` to get the headers for the particular set
      of labs):

      .. code-block:: python

         class MyTagRecords(TagRecords):
             """A custom TagRecords class"""
         
             labs = [
                 "lab1",
                 "lab2"
             ]
             headers = get_tag_headers(labs)

      Instances of the resulting class will have the attributes ``lab1``
      and ``lab2``, each of which contain a
      :py:class:`~records.tag_record.TagRecord`. If a
      lab is provided such that the name cannot be accessed as an object
      attribute using the dot syntax, users should use ``getattr`` and
      ``setattr`` appropriately to access the attributes.

   .. automethod:: to_strings

   .. automethod:: from_strings
```