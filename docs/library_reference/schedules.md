# Schedules

```{eval-rst}
To schedule a flow with a flow manager, users must specify a
:py:class:`~flow.schedule.Schedule` that an associated flow should be run
on. The base :py:class:`~flow.schedule.Schedule` class allows users to
specify this by providing a function to check whether the flow should be
run, given the current time:

.. autoclass:: flow.schedule.Schedule()

   .. automethod:: __init__
```

In addition, helper children classes are implemented for common schedule
patterns:

```{eval-rst}
.. autoclass:: flow.schedule.Always()

   .. automethod:: __init__

.. autoclass:: flow.schedule.Hourly()

   .. automethod:: __init__

.. autoclass:: flow.schedule.Daily()

   .. automethod:: __init__

.. autoclass:: flow.schedule.Weekly()

   .. automethod:: __init__
```