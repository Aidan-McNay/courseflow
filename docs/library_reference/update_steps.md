# Update Steps

## Base Class

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