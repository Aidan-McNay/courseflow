# flow

Utilities for making an object-oriented course management flow.

## Objects

There are five main objects included in our structure:

 - `AdminFlow`
 - `AdminRecordStep`
 - `AdminUpdateStep`
 - `AdminPropagateStep`
 - `RecordStorer`

## Main Flow

An `AdminFlow` represents an entire administrative flow. This should
represent a set of actions to take. The flow can be run by calling

```python
flow.run()
```

In addition, our flow can be configured by running

```python
flow.config(config_dict)
```

This will configure the flow and all steps it contains appropriately based
on the given configuration dictionary. To determine what configurations
the flow expects, one can use

```python
flow.describe_config()
```

This will produce a dictionary where all elements are strings including
the type and description of the configuration. Each step will also contain
a `_description` element; this isn't needed by the flow when configuring,
but is given in the description to be more verbose.

## Records

Our flows operate on array of a generic record type (referenced as `T`); 
this is how we maintain state between runs. Steps are templated to only
support records of a specific type.

Records are provided to and stored by the flow via a `RecordStorer`: 
the flow will call

```python
record_storer.get_records(logger: Callable[[str], None])
```

to obtain the current known records, and will later call 

```python
record_storer.set_records(
  rec_list: list[T], 
  logger: Callable[[str], None]
)
```
to store the records. The `RecordStorer` is responsible for managing how
these records are stored and accessed.

## Steps

A flow is composed of multiple steps:

 - An `AdminRecordStep` is used to add any records to the total list of
   records
 - An `AdminUpdateStep` is used to update the known state (contained in
   the recordss).
 - An `AdminPropagateStep` is used to propagate the current state - it
   uses the state to make any necessary changes (updating state if 
   necessary)

The key difference is that `AdminUpdateStep`s should never cause any
changes outside of the flow, whereas `AdminPropagateStep`s may make
external changes (ex. via API calls).

All steps are constructed within the flow (using their configurations), so
we only inform the flow of the class of the step, letting the flow do the
construction.

An `AdminRecordStep` is added to the flow using `flow.add_record_step`,
which has the following signature

```python
flow.add_record_step(name: str, step: Type[AdminRecordStep])
```

 - `name`: A string representing the step's name
 - `step`: The `AdminRecordStep` class for a new record step

Unlike other steps, `AdminRecordStep`s are executed serially in the order
they are added, to make sure that each `AdminRecordStep` is aware of other
records that were added, before making changes of its own.

Other steps may be added via `flow.add_update_step` or 
`flow.add_propagate_step`, respectively. These have a similar signature:

```python
flow.add_update_step(
  name: str, 
  step: Type[AdminUpdateStep],
  depends_on: list[str] = []
)
flow.add_propagate_step(
  name: str, 
  step: Type[AdminPropagateStep], 
  depends_on: list[str] = []
)
```

 - `name`: A string representing the step's name
 - `step`: The `AdminUpdateStep` or `AdminPropagateStep` class for the
     step
 - `configs`: The configuration dictionary given for the step
 - `depends_on`: A list of names of other steps (of the same
     type) that the step depends on. This is used to safely multithread
     steps and achieve high-speed parallelism between tasks. If a dependency
     isn't enabled, it will be treated as though it has completed

## How Steps are Called

`AdminRecordStep`s are called with the following signature:

```python
record_step.new_records(
  curr_records: list[T],
  logger: Callable[[str], None],
  set_metadata: Callable[[str, object], None],
  debug: bool = False
) -> list[T]
```

This should take in the current records, and update them (add/remove
records) as necessary.

 - `logger` is a function to call to log specific events from the step
 - `debug` indicates whether we are operating in "debug" mode. In this
   mode, the step can inject debug data to reflect a particular scenario

`AdminUpdateStep`s and `AdminPropagateStep`s are called similarly:

```python
update_step.update_records(
  records: list[tuple[T, threading.Lock]],
  logger: Callable[[str], None],
  get_metadata: Callable[[str], object],
  set_metadata: Callable[[str, object], None],
  debug: bool = False
) -> None

propagate_step.propagate_records(
  records: list[tuple[T, threading.Lock]],
  logger: Callable[[str], None]
  get_metadata: Callable[[str], object],
  debug: bool = False
) -> None
```

These functions shouldn't return anything, but should instead manipulate
the existing record objects. Records are provided with an associated
lock; steps must make sure to acquire the associated lock before
accessing a given record.

`set_metadata` can be used by `AdminUpdateStep`s to give a piece of data a
global name, which can then be retrieved by `AdminPropagateStep`s through 
`get_metadata`. It is undefined for two `AdminUpdateStep`s to call their 
`set_metadata` functions with the same identifier; care should be taken to
make identifiers unique. In addition, `get_metadata` will always return a
piece of data of type `Any`, so `AdminPropagateStep`s must manually check
the type.

Notably, when `debug = True`, `AdminPropagateStep`s are NOT allowed to
modify any external state, but should instead communicate their intent to
do so through the logger. It is __imperative__ that designers abide by
this convention.

Calls to `update_records` and `propagate_records` will be multithreaded
with other calls to the same function from other steps. However, step
implementations may treat the metadata functions and accesses to records as
thread-safe without implementing more concurrency primitives.

