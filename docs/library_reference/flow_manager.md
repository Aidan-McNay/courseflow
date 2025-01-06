# Flow Manager

```{eval-rst}
A :py:class:`~flow.flow_manager.FlowManager` is used to associate
:py:class:`~flow.flow.Flow`\ s with
:py:class:`~flow.schedule.Schedule`\ s, and run them accordingly.

.. autoclass:: flow.flow_manager.FlowManager()

   .. automethod:: __init__

      Flow will only be run in parallel when ``pathos`` is installed
      (see :py:meth:`~flow.flow_manager.FlowManager.run`)

   .. automethod:: add_unconf_flow

      Note that flows are configured/validated automatically when added,
      such that all flows are validated before any are run

   .. automethod:: add_conf_flow

   .. automethod:: run

      :py:class:`~flow.flow_manager.FlowManager` uses ``pathos`` to run
      :py:class:`~flow.flow.Flow`\ s in parallel, across multiple processes.
      This is necessary (using ``pathos`` instead of
      the built-in ``multiprocessing`` library) because flow instances (not
      to mention their dynamically-defined configuration types) cannot be
      pickled with ``pickle``, and must instead by pickled with ``dill``.
      If ``pathos`` is not present, :py:class:`~flow.flow.Flow`\ s will be
      run serially
```