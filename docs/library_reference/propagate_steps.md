# Propagate Steps

## Base Class

```{eval-rst}
All propagate steps must inherit from/implement the following base class
(with some repeated from :py:class:`~flow.flow_steps.FlowStep`)

.. autoclass:: flow.flow_steps.FlowPropagateStep()

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

   .. automethod:: propagate_records
```

## Implementations

```{eval-rst}
.. autoclass:: canvas_steps.assign_groups.AssignGroups()

   This step takes in a current Canvas group
   (likely with some self-grouping), and pairs up remaining students to
   form lab groups. Groups are made to ensure that pairs are in the same
   lab section. Odd numbers are resolved by forming a group of three.

   Note that current groups are **NOT** checked to see whether they are
   groups of fewer than three; the Canvas group can be configured to
   restrict this. However, solo students in a group are removed and
   re-assigned. This also has the side-benefit that if a student drops,
   the remaining partner is re-assigned to another group automatically.
   If an instructor wishes to disable this, they should disable the
   step.

   The Canvas group (as well as our records) will be updated with the new
   group mapping.

   Supported record types: :py:class:`~records.student_record.StudentRecord`

   Sets metadata: :py:attr:`old_groups`
```

```{eval-rst}
.. autoclass:: utils.basic_steps.BasicPropagateStep()

   Supported record types: ``int``
```

```{admonition} Under construction
:class: warning

Many of the implemented propagate steps are under construction - stay
tuned!
```