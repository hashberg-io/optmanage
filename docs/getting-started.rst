Getting Started
===============

.. _getting-started:

Flexible option managers, supporting options with default values, static type hints, runtime type checking, and custom runtime validation logic.
You can install the latest release from `PyPI <https://pypi.org/project/optmanage/>`_:

.. code-block:: console

    $ pip install -U optmanage

The library requires Python 3.15 or later.

Defining options
----------------

Custom option manager classes are created by subclassing :class:`~optmanage.manager.OptionManager` and using the :class:`~optmanage.option.Option` descriptor to define options as class attributes.
An option manager is then obtained by instantiating the option manager class:

.. code-block:: python

    from collections.abc import Mapping
    from typing import Literal
    from optmanage import Option, OptionManager

    class MyOptions(OptionManager):
        """Options of some library."""

        validate = Option(bool, True)
        """Whether to validate arguments to functions and methods."""

        eq_atol = Option(float, 1e-8, lambda x: x >= 0)
        """Absolute tolerance used for equality comparisons."""

        scaling = Option(
            Mapping[Literal["x", "y", "z"], float],
            {"x": 1.0, "y": 2.0, "z": 1.0},
            lambda scaling: all(v >= 0 for v in scaling.values()),
        )
        """Scaling for coordinate axes used in plots."""

    options = MyOptions()

Each option takes a type, a default value, and an optional validator function:

.. code-block:: python

    validate = Option(bool, True)
    #     option type ^^^^  ^^^^ default value

    eq_atol = Option(float, 1e-8, lambda x: x >= 0)
    #           optional validator ^^^^^^^^^^^^^^^^

Any type supported by the `typing-validation <https://github.com/hashberg-io/typing-validation>`_ library can be used for options, including type hints such as ``Mapping[Literal["x", "y", "z"], float]`` above.
Unsupported types are rejected with :exc:`TypeError` when the option is created, and the default value is validated at the same time.

Validation
----------

Every value is checked against the type of its option at runtime, and a value of the wrong type is rejected with :exc:`TypeError`.
If a validator is given, it is then called on the value, which is rejected with :exc:`ValueError` if the validator returns :obj:`False` or raises an exception; in the latter case, the :exc:`ValueError` is raised from the validator's exception.
Any other return value, including :obj:`None`, accepts the value, so validators can be either predicates or functions which raise on invalid values:

.. code-block:: python

    def check_tolerance(x: float) -> None:
        if x < 0:
            raise ValueError("Tolerance must be non-negative.")

    eq_atol = Option(float, 1e-8, check_tolerance)

Setting options
---------------

Options can be accessed and set like attributes of the ``options`` object, or by name:

.. code-block:: python

    print(options.scaling)  # {'x': 1.0, 'y': 2.0, 'z': 1.0}
    options.scaling = {"x": 2.5, "y": 1.5, "z": 1.0}
    print(options["scaling"]) # {'x': 2.5, 'y': 1.5, 'z': 1.0}
    options["eq_atol"] = 1e-6

Access by name raises :exc:`KeyError` for names which are not options.

Assigning to an attribute which is neither an option nor declared by the class raises :exc:`AttributeError`, so that misspelt option names are not silently accepted:

.. code-block:: python

    options.valdiate = False
    # AttributeError: 'MyOptions' has no option 'valdiate', and other attributes
    # must be declared by the class. Did you mean '.validate' instead of '.valdiate'?

Subclasses which need further instance attributes declare them in the class body, as annotations, slots, properties or class attributes:

.. code-block:: python

    class MyLabelledOptions(MyOptions):
        label: str

        def __init__(self, label: str) -> None:
            self.label = label

Names which belong to :class:`~optmanage.manager.OptionManager` itself, such as ``set`` or ``keys``, cannot be assigned on instances.
Option names and values can be iterated with :meth:`~optmanage.manager.OptionManager.keys`, :meth:`~optmanage.manager.OptionManager.values` and :meth:`~optmanage.manager.OptionManager.items`.

Multiple options can be set together using the :meth:`~optmanage.manager.OptionManager.set` method, which returns the previous values of the options.
All values are validated before any of them is set, so a failed call leaves every option unchanged:

.. code-block:: python

    options.set(validate=False, eq_atol=1e-3)
    print(options.validate) # False
    print(options.eq_atol)  # 0.001

Temporary values
----------------

The ``options`` object can be called to obtain a context manager which sets options temporarily, restoring their previous values when the context exits, including on exceptions.
Contexts can be nested:

.. code-block:: python

    with options(validate=False, eq_atol=1e-3):
        print(options.validate) # False
        print(options.eq_atol)  # 0.001
    print(options.validate) # True
    print(options.eq_atol)  # 1e-08

While an option has a temporary value, it cannot be set or reset permanently: attempting to do so raises :exc:`ValueError`.

Temporary values are stored on the option manager itself, so they are visible to all threads and asynchronous tasks using it.
Concurrent code which sets temporary values on a shared option manager must coordinate their use, and must exit the contexts in the reverse order of entry.

Resetting options
-----------------

All options can be reset to their default values with the :meth:`~optmanage.manager.OptionManager.reset` method, which returns their previous values:

.. code-block:: python

    options.set(validate=False, eq_atol=1e-3)
    options.reset()
    print(options.validate) # True
    print(options.eq_atol)  # 1e-08

An individual option can be reset with the :meth:`~optmanage.option.Option.reset` method of the :class:`~optmanage.option.Option` object, accessed from the option manager class:

.. code-block:: python

    options.set(validate=False, eq_atol=1e-3)
    MyOptions.eq_atol.reset(options) # resets 'eq_atol' on the 'options' object
    print(options.validate) # False
    print(options.eq_atol)  # 1e-08

Inheritance
-----------

Option manager classes inherit the options of their option manager base classes, including under multiple inheritance.
Class definitions which would make the options of a class ambiguous raise :exc:`TypeError`, namely:

- defining an option with the same name as an inherited option, or as an attribute of :class:`~optmanage.manager.OptionManager` (such as ``set`` or ``keys``);
- inheriting distinct options with the same name from different base classes;
- overriding an inherited option with an attribute which is not that option;
- binding the same :class:`~optmanage.option.Option` object more than once, or binding it to a class which is not a subclass of :class:`~optmanage.manager.OptionManager`.

Copying and pickling
--------------------

Option managers support :mod:`copy` and :mod:`pickle`.
The copy holds the permanent values of the options, without the temporary values of any active context, and is independent of the original.

GitHub repo: https://github.com/hashberg-io/optmanage
