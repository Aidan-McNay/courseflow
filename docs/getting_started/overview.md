# Overview

`cornell-canvas` is a framework for managing Cornell classes across a
variety of platforms, including Google Sheets and GitHub. It implements
several wrappers around API calls, and integrates different pieces of
functionality together to autonomously manage a course. Finally, it also
provides one-off scripts for expediting common tasks that users may wish
to perform manually

## Records

It is useful to consider discrete objects of information, to consider
how they should move through different processing steps in our scripts.
In the documentation, you will see these referenced as _records_. A
record is a collection of information that is passed between different
steps; an example might be a object containing a student's name, NetID,
and lab section.

## Steps

`cornell-canvas`'s functionality is centered around __flow steps__. A
flow step performs a single operation on course data, in the form of a
record. Examples include emailing a student based on their course
standing, or adding a student to a GitHub repo based on their Canvas group.

Flow steps must have the `description` and `config_types` attributes,
and must implement the `validate` function at a baseline:

```python
class MyFlowStep(FlowStep):
  """A custom FlowStep."""
  description = "A custom FlowStep"

  config_types = [
    "user", str, "The name of the user running the flow"
  ]

  def validate(self: typing.Self) -> None:
    if self.configs.user != "Aidan":
      raise Exception("You aren't Aidan!")
```

 - `description`: A high-level discription of what the step does
 - `config_types`: The name, type, and description of all
     configurations that the step needs. The type should be a _flat_
     type (a.k.a. not a collection), such that it can be checked with
     `isinstance`. Currently supported configuration types are `int`,
     `str`, `bool`, and `datetime.datetime`
 - `validate`: A function fo validate configurations (without running
     the step). If the configurations aren't "valid" (where validity
     differs based on the semantics of each step), `validate` should
     raise an exception

```{eval-rst}
The base class :py:class:`~flow.flow_steps.FlowStep` implements the
``__init__`` method, such that all configurations are included in a
``configs`` attribute for each step object when it's instantiated (with
each configuration being appropriately typed). In addition, the above
attributes allow a :py:class:`~flow.flow_steps.FlowStep` to dump its
high-level description and configurations into template configuration
files, allowing users to get an example of what the expected
configurations might look like.

.. admonition:: Why class attributes?
   :class: note

   The above configurations are specified as part of the class, not of a
   particular instance. When extending the flow, if you want a
   :py:class:`~flow.flow_steps.FlowStep` that performs a different
   high-level action (beyond configurations), you will need to implement a
   new :py:class:`~flow.flow_steps.FlowStep`. Having the configurations as
   part of the class:

    * Helps extenders of the class by forcing configurations to be checked
      upon step instantion, causing faulty configurations to be caught
      early-on before any other steps have run
    * Allows documentation to be generated for a step without an instance
      of the class
    * Allows for robust type checking and type annotation
    * Makes sense semantically; the functionality and expected configurations
      of a step should be engrained as part of its type, not checked for a
      particular instance

In addition to a base :py:class:`~flow.flow_steps.FlowStep`, four more
abstract classes are defined to further define the semantics of a step,
based on how they interact with records:

 - A :py:class:`~flow.flow_steps.FlowRecordStep` **generates** records. It
   takes in a current list of records, and possibly adds records to the
   list, returning the new list. For example, a
   :py:class:`~flow.flow_steps.FlowRecordStep` might look at the current
   Canvas enrollment, and add records for any student not already in the
   list of records.
 - A :py:class:`~flow.flow_steps.FlowUpdateStep` **updates** records. It
   takes in a current list of records, and updates the records based on
   current information. For example, a
   :py:class:`~flow.flow_steps.FlowUpdateStep` might look at each record,
   and update it with the student's current submission to a Canvas quiz. 
   A :py:class:`~flow.flow_steps.FlowUpdateStep` **DOES NOT** update any
   external entity about the information in records. Instead, it should
   check the gathered information, and generate any necessary exceptions
   (although ideally, a :py:class:`~flow.flow_steps.FlowUpdateStep` would
   handle any exceptions itself).
 - A :py:class:`~flow.flow_steps.FlowPropagateStep` **propagates** the
   data in records to external entities, such as Canvas and GitHub. For
   example, a :py:class:`~flow.flow_steps.FlowPropagateStep`
   might see that a record indicates a missing submission from a student,
   and would email the student about that submission. A
   :py:class:`~flow.flow_steps.FlowPropagateStep` should ideally never
   generate any exceptions; any faulty configurations should be caught
   with ``validate``, and any faulty data should be caught by the
   :py:class:`~flow.flow_steps.FlowUpdateStep` that added it. Like
   :py:class:`~flow.flow_steps.FlowUpdateStep`, 
   a :py:class:`~flow.flow_steps.FlowPropagateStep` is allowed to modify
   record data, primarily to indicate that propagation to external
   entities has occurred.
 - A :py:class:`~flow.record_storer.RecordStorer` is used to store
   records; we'll cover them more with flows.

.. admonition:: Update vs. Propagate
   :class: note

   A key note is the difference between a
   :py:class:`~flow.flow_steps.FlowUpdateStep` and a
   :py:class:`~flow.flow_steps.FlowPropagateStep`; the former should add
   and check any incoming data, whereas the latter uses said data to
   update other external entities, such as Canvas and GitHub. These are
   separated such that all :py:class:`~flow.flow_steps.FlowUpdateStep`
   instances occur before any
   :py:class:`~flow.flow_steps.FlowPropagateStep` instances, ensuring that
   any exceptions are caught before external state is modified (similar to
   a processor's commit point). While this somewhat limits expressibility,
   we haven't found this to be a practical issue, and workarounds can be
   implemented with multiple flows.

These steps each additionall require child classes to implement either
:py:meth:`~flow.flow_steps.FlowRecordStep.new_records`,
:py:meth:`~flow.flow_steps.FlowUpdateStep.update_records`, or
:py:meth:`~flow.flow_steps.FlowPropagateStep.propagate_records`, respectively.
Consult the class reference for more details. Extensions of the framework
should inherit from these three classes, in order to be integrated into a
:py:class:`~flow.flow.Flow`
```

## Flows

A `Flow` is a sequence of `FlowStep`s to be executed in order to achieve a
high-level goal. `FlowRecordStep`s, `FlowUpdateStep`s, and
`FlowPropagateStep`s can all be added to a `Flow`; the relevant class is
provided (as configurations aren't available to instantiate with), as well
as a name for the particular step. A particular step can be added multiple
times to a flow, such that each named instance can be configured
differently.

A `Flow` runs its steps as follows:

 1. All `FlowRecordStep`s are run sequentially (to ensure that all updates
    from a given step are known to subsequent step, in the case that two
    `FlowRecordStep`s may want to add the same record)
 2. All `FlowUpdateStep`s are run in parallel; the degree of parallelism
    can be specified by flow's `num_threads` configuration. Lock striping
    is used to ensure safety; records are provided as a list of tuples
    containing a record and a lock, and each step should acquire the lock
    before acting on/updating the respective record
 3. All `FlowPropagateStep`s are run in parallel, similar to
    `FlowUpdateStep`s

Depending on the semantics, a user may wish to specify additional
dependencies/orderings between `FlowUpdateStep`s or `FlowPropagateStep`s.
`Flow`s allow this by allowing a list of dependency step names to be
specified when adding one of these steps to a flow, such that a step will
not be allowed to run until all of the dependency steps have completed.
`Flow`s will check that dependency steps have already been added to the
flow, preventing deadlock by forcing the dependency tree to be a directed
acyclic graph (DAG).

```{image} imgs/example-flow-execution.jpg
:alt: An example execution timeline of a flow
:width: 50%
:align: center
```

## Record Storers

Aside from adding to, updating, and propagating lists of records, a flow
also needs to be able to store records. This is abstracted away with a
`RecordStorer`, an abstract class that inherits from `FlowStep`. In
addition to the required attributes for a `FlowStep`, a `RecordStorer`
must implement the following two methods:

 - `get_records`: This is used to access the list of records from
     wherever/however they're stored, and is used at the start of a
     `Flow` to get the pre-existing list of records
 - `set_records`: This is used to store the (new) list of records at
     the end of a `Flow`, after they have been processed by the other
     steps

```python
class MyRecordStorer(RecordStorer):
    """A custom RecordStorer."""
    
    ...

    def get_records(
        self: Self, logger: Callable[[str], None], debug: bool = False
    ) -> list[RecordType]:
        ...

    def set_records(
        self: Self,
        rec_list: list[RecordType],
        logger: Callable[[str], None],
        debug: bool = False,
    ) -> None:
        ...
```

### Metadata

Data is primarily passed between steps through records. However, steps
may also want to communicate data that isn't reflected in a record, such
as events that have already occurred in a flow. This data is referred to
as _metadata_. `Flow`s provide mechanisms for `FlowStep`s to access
metadata from the flow. When called to perform their specific action,
`FlowStep`s are provided with:

 - `set_metadata` (`typing.Callable[[str, typing.Any], None]`): A function
   to associate any object with a particular name for the overall flow
 - `get_metadata` (`typing.Callable[[str], typing.Any]`): A function to
   retrieve the data associated with a particular name for a flow. If the
   name has no data associated with it, `None` is returned

```python
set_metadata("course_number", 2300)

...

num = get_metadata("course_number") # num holds 2300
```

This allows `FlowStep`s to comunicate arbitrary data between each other.
However, this introduces a number of other considerations:

 - To support arbitrary data, `get_metadata` returns an object of type
   `typing.Any`. To be type-safe, each `FlowStep` must dynamically type
   check the returned data (or use `typing.cast`, although this isn't
   preferred and may lead to bugs from non-rigorous type checking)
 - Whether a data exists or not depends on the ordering of steps. If this
   dependency exists between two `FlowUpdateStep`s or two
   `FlowPropagateStep`s, the dependency must be specified in the flow to
   ensure reproducible ordering in the DAG (requiring appropriate
   documentation)
 - Steps accessing a particular piece of data must be sure to use the same
   name as the step that set the data

## Configuring Flows

Once we have a flow, we need to be able to configure it for our specific
needs. All `Flow`s have a `config` method that takes in a dictionary
configuratioin for the flow, and configures each step appropriately. Each
step should have a different entry in the configuration dictionary with
all of its configurations. The flow will check that all necessary
configurations are present (of the correct type), and will instantiate all
steps with their configurations. Once configured, a flow can be run using
the `run` method.

While it is possible to ascertain the necessary configurations from the
flow and its construction, `Flow`s additionally provide a
`describe_config` method to make this process easier. For a constructed
`Flow`, this method will produce a dictionary of identical structure to
the expected configuration, where each entry is a description of what is
expected in the configuration. See the
[tutorial](tutorial.md) for more details.

### Step Modes

In addition to each `FlowStep`'s configurations, a _mode_ is expected for
each step. Each step can be configured in one of three modes:

 - `include`: This should be the default mode, and runs the step
     "normally"
 - `debug`: When a step is run in debug mode, its operation may differ
     slightly. This is up to each individual step, but may include
     providing sample data and/or more verbose output

     ```{admonition} Propagate Steps in debug
     :class: caution

     When run in debug, `FlowPropagateStep`s should __never__ actually
     modify external state (as doing so on debug data may be incorrect,
     as well as because we may not wish to perform updates when debugging
     a script). Instead, such steps should use their `logger` to indicate
     their intent to modify state, but not actually do so
     ```

  - `exclude`: The step is excluded, and will not be run. Dependencies on
      excluded steps are removed from DAGs

      ```{admonition} Record Storing

     Because of their central role in a flow, a `Flow`'s `RecordStorer`
     cannot be excluded
     ```

## Flow Managers

```{admonition} _Under construction!_
:class: warning
Flow Managers are currently being implemented, and will be ready shortly
```