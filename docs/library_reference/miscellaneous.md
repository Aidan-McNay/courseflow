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

## Classes

```{eval-rst}
.. autoclass:: records.tag_record.TagRecord

   .. automethod:: tagged
```