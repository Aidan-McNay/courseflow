# Update Steps

## Base Class

```{eval-rst}
All update steps must inherit from/implement the following base class
(with some repeated from :py:class:`~flow.flow_steps.FlowStep`)

.. autoclass:: flow.flow_steps.FlowUpdateStep()

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

   .. automethod:: update_records
```

## Implementations

```{eval-rst}
.. autoclass:: utils.basic_steps.BasicUpdateStep()

   Supported record types: ``int``

   .. py:attribute:: configs.increment
      :type: int

      The amount to increment records by
   
   .. automethod:: validate

      Specifically, we make sure that the supplied increment amount is
      positive
```