# Flow

`courseflow` has one `Flow` class. Steps are added to particular
instances of `Flow`s to construct different flows with different
functionalities.

```{eval-rst}
.. autoclass:: flow.flow.Flow[RecordType]()

   .. automethod:: __init__

   .. automethod:: silent

   .. automethod:: verbose

   .. automethod:: logfile

   .. automethod:: add_record_step

   .. automethod:: add_update_step

   .. automethod:: add_propagate_step

   .. automethod:: describe_config

   .. automethod:: config

   .. automethod:: run
```