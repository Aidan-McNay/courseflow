# Miscellaneous

The following functions and classes are documented not as part of the core
flow library, but for completeness/reference.

## Functions

```{eval-rst}
.. autofunction:: flow.run_flow.run_flow

   When running the flow as a main program, the following flags are
   available:

   **Flow Arguments:**

   * ``-d``, ``--dump`` ``YAML_FILE``: Dump the configuration description
     to the specified file
   * ``-r``, ``--run`` ``YAML_FILE``: Run the flow with the configurations
     in the given file
   * ``-v``, ``--validate`` ``YAML_FILE``: Validate (but do not run) the
     flow with the configurations in the given file

   **Other Arguments:**

   * ``-l``, ``--logfile`` ``LOGFILE``: Add a path to log the flow's
     output to
   * ``-s``, ``--silent``: Prevent the flow from outputting to the command
     line
   * ``-h``, ``--help``: Show the program's usage and exit
```

```{eval-rst}
.. autofunction:: records.tag_record.get_tag_headers
```

```{eval-rst}
.. autofunction:: github_steps.tag_repo.get_tagger

   For example, to add a tagger to a :py:class:`~flow.flow.Flow` named
   ``tag-lab1.1`` that tags all personal repos for the ``lab1.1`` submission,
   one could do the following:

   .. code-block:: python

      flow.add_propagate_step(
          "tag-lab1.1", get_tagger("lab1.1", "personal", LabTagRecords)
      )

   See :py:class:`~github_steps.tag_repo.RepoTagger` for information on
   the generated/returned class type.
```

## Classes

```{eval-rst}
.. autoclass:: flow.flow_steps.ValidConfigTypes
```

```{eval-rst}
.. py:class:: FlowStep()
   :module: flow.flow_steps
   
   A base class representing an abstract step in our flow.

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
      (respectively).

   Based on the ``config_types``, an instance of the class will have an
   attribute ``configs`` with each described configuration. For example,
   if ``config_types`` is defined as

   .. code-block:: python

      config_types = [
        ("test", int, "A test configuration")
      ]

   then instances of the class will have an attribute ``configs.test`` of
   type ``int``

   .. automethod:: validate

      This function should inspect the object's ``configs`` attribute, and
      perform any static validation possible. :py:func:`validate` is
      always called on object initialization to ensure that configurations
      are always valid
```

```{eval-rst}
.. autoclass:: records.tag_record.TagRecord

   .. automethod:: tagged
```