# Tutorial

This tutorial will walk you through using the framework. You'll gain
experience building a flow completely, configuring the flow, and then
swapping out steps for ones of your own design!

```{admonition} Tutorial Actions
:class: tip

You will see cards similar to this one throughout the tutorial. These
indicate actions that you should take as part of the tutorial
```

The tutorial assumes that you have already completed all of the
[installation steps](installation.md). No API key setup is required.

## Building a Flow

We'll get started by building a basic flow. `cornell-canvas` has
implemented "basic" steps (in `utils.basic_steps`) for this purpose,
to serve as minimal examples as to what each step needs to do. These may
also be useful later to reference when building your own steps!

```{eval-rst}
.. admonition:: Starting our Python script
   :class: tip

   Let's start our flow by importing the different steps we'll need. For
   this tutorial, we'll be using:

   * A few steps from `utils.basic_steps`
   * The main `Flow` class
   * A helper function :py:func:`~flow.run_flow.run_flow`, which runs our
     flow as a program, and provides argument parsing to interact with the
     flow

   Open up a new Python file using your preferred code editor, named
   ``basic_flow.py``, and put the following imports at the top:

   .. code-block:: python

      from utils.basic_steps import (
          BasicRecordStorer,
          BasicRecordStep,
          BasicUpdateStep,
          BasicPropagateStep,
      )
      from flow.flow import Flow
      from flow.run_flow import run_flow
```

### Overall Flow and Record Storer

```{eval-rst}
The first thing to do is to construct a :py:class:`~flow.flow.Flow`. Each
flow needs a ``RecordStorer``; for this tutorial, we'll use
:py:class:`~utils.basic_steps.BasicRecordStorer`, which stores integers in
a file

.. admonition:: Instantiating a Flow
   :class: tip
   
   Let's create a flow! In `basic_flow.py`, instantiate a flow as
   ``basic_flow`` like the following:

   .. code-block:: python

      basic_flow = Flow(
          name="basic-flow",
          description=("A basic flow to access and manipulate integer records"),
          record_storer_type=BasicRecordStorer,
          record_storer_name="basic-storer",
      )

   Here, we're specifying:

   * The new flow is named ``basic-flow``
   * The flow's high-level description is to access and manipulate integers
   * The flow's record storer is a :py:class:`~utils.basic_steps.BasicRecordStorer`,
     given the name ``basic-storer``

   Note that a ``Flow`` needs to know what type of records it operates on;
   it's generic across record types, seen in the documentation as
   ``RecordType``. Here, the flow can figure out that it operates on
   integers based on that :py:class:`~utils.basic_steps.BasicRecordStorer`
   can only operate on integers, but explicitly specifying the type of
   records using the following syntax would also be valid:

   .. code-block:: python

      basic_flow = Flow[int](
          name="basic-flow",
          description=("A basic flow to access and manipulate integer records"),
          record_storer_type=BasicRecordStorer,
          record_storer_name="basic-storer",
      )
```

### Adding a Record Step

```{eval-rst}
For this tutorial, we'll use
:py:class:`~utils.basic_steps.BasicRecordStep` to supply records. This
record step always appends a new integer record (random between 0 and 10)
to the list of records.

.. admonition:: Adding a :py:class:`~utils.basic_steps.BasicRecordStep`
   :class: tip
   
   To add this step to your flow, use the
   :py:meth:`~flow.flow.Flow.add_record_step` method of the flow. Add the
   following to ``basic_flow.py`` to add an instance of this step named
   ``new-integer``:

   .. code-block:: python

      basic_flow.add_record_step("new-integer", BasicRecordStep)

.. admonition:: Matching Record Types:
   :class: note

   Here, notice that :py:class:`~utils.basic_steps.BasicRecordStep`
   operates on ``int`` records, the same as the overall flow. If these
   didn't match, our linter would throw an error during type-checking.
   The same goes for all other steps that we add.
```

### Adding an Update Step

### Adding a Propagate Step

## Configuring the Flow

## Implementing New Steps