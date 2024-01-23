Getting Started
===============

.. _getting-started:

You can install the latest release from `PyPI <https://pypi.org/project/optmanage/>`_ as follows:

.. code-block:: console

    $ pip install --upgrade optmanage

Custom option manager classes can be created by subclassing :class:`~optmanage.manager.OptionManager` and using the :class:`~optmanage.option.Option` descriptor to set options.
An option manager object can then be obtained by instantiating the option manager class:

.. code-block:: python

    from optmanage import Option, OptionManager

    class MyOptions(OptionManager):
        """ Options of some library. """

        validate = Option(bool, True)
        """ Whether to validate arguments to functions and methods. """

        eq_atol = Option(float, 1e-8, lambda x: x >= 0)
        """ Absolute tolerance used for equality comparisons."""

        scaling: Option(
            Mapping[Literal["x", "y", "z"], float],
            {"x": 1.0, "y": 2.0, "z": 1.0},
            lambda scaling: all(v >= 0 for v in scaling.values())
        )
        """ Scaling for coordinate axes used in plots.  """

    options = MyOptions()


Each option takes a default value, a type, and an optional validator function:

.. code-block:: python

    validate = Option(bool, True)
    #     option type ^^^^  ^^^^ default value

    eq_atol = Option(float, 1e-8, lambda x: x >= 0)
    #           optional validator ^^^^^^^^^^^^^^^^

Any type supported by the `typing-validation <https://github.com/hashberg-io/typing-validation>`_ library can be used for options, including `PEP 484 <https://peps.python.org/pep-0484/>`_ type hints:

.. code-block:: python

    scaling: Option(
        Mapping[Literal["x", "y", "z"], float], # <- type hints supported
        {"x": 1.0, "y": 2.0, "z": 1.0},
        lambda scaling: all(v >= 0 for v in scaling.values())
    )

Options can be accessed and set like attributes of the ``options`` object:

.. code-block:: python

    print(options.scaling)  # {'x': 1.0, 'y': 2.0, 'z': 1.0}
    options.scaling = {"x": 2.5, "y": 1.5, "z": 1.0}
    print(options.scaling) # {'x': 2.5, 'y': 1.5, 'z': 1.0}

It is possible to set multiple options simultaneously using the :meth:`~optmanage.manager.OptionManager.set` method of the ``options`` object:

.. code-block:: python

    options.set(validate=False, eq_atol=1e-3)
    print(options.validate) # False
    print(options.eq_atol)  # 0.001

It is also possible to use the options object as a context manager, for temporary option setting:

.. code-block:: python

    with options(validate=False, eq_atol=1e-3):
        print(options.validate) # False
        print(options.eq_atol)  # 0.001
    print(options.validate) # True
    print(options.eq_atol)  # 0.00000001

All options can be reset to their default values by using the :meth:`~optmanage.manager.OptionManager.reset` method of the ``options`` object:

.. code-block:: python

    options.set(validate=False, eq_atol=1e-3)
    print(options.validate) # False
    print(options.eq_atol)  # 0.001
    options.reset()
    print(options.validate) # True
    print(options.eq_atol)  # 0.00000001

An individual option can be reset to its default value by using the :meth:`~optmanage.option.Option.reset` method of the :class:`~optmanage.option.Option` object, accessed from the option manager class:

.. code-block:: python

    options.set(validate=False, eq_atol=1e-3)
    print(options.validate) # False
    print(options.eq_atol)  # 0.001
    MyOptions.eq_atol.reset(options) # resets 'eq_atol' on the 'options' object
    print(options.validate) # True
    print(options.eq_atol)  # 0.001

GitHub repo: https://github.com/hashberg-io/optmanage
