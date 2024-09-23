optmanage: A library to create flexible option managers.
========================================================

.. image:: https://img.shields.io/badge/python-3.10+-green.svg
    :target: https://docs.python.org/3.10/
    :alt: Python versions

.. image:: https://img.shields.io/pypi/v/optmanage.svg
    :target: https://pypi.python.org/pypi/optmanage/
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/status/optmanage.svg
    :target: https://pypi.python.org/pypi/optmanage/
    :alt: PyPI status

.. image:: http://www.mypy-lang.org/static/mypy_badge.svg
    :target: https://github.com/python/mypy
    :alt: Checked with Mypy

.. image:: https://readthedocs.org/projects/optmanage/badge/?version=latest
    :target: https://optmanage.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://github.com/hashberg-io/optmanage/actions/workflows/python-pytest.yml/badge.svg
    :target: https://github.com/hashberg-io/optmanage/actions/workflows/python-pytest.yml
    :alt: Python package status

.. image:: https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square
    :target: https://github.com/RichardLitt/standard-readme
    :alt: standard-readme compliant


Flexible option managers, supporting options with default values, static type hints, runtime type checking, and custom runtime validation logic.

.. contents::


Install
-------

You can install the latest release from `PyPI <https://pypi.org/project/optmanage/>`_ as follows:

.. code-block:: console

    $ pip install --upgrade optmanage


Usage
-----

Custom option manager classes can be created by subclassing `OptionManager <https://optmanage.readthedocs.io/en/latest/api/optmanage.manager.html#optionmanager>`_ and using the `Option <https://optmanage.readthedocs.io/en/latest/api/optmanage.option.html#option>`_ descriptor to set options.
An option manager object can then be obtained by instantiating the option manager class:

.. code-block:: python

    from optmanage import Option, OptionManager

    class MyOptions(OptionManager):
        """ Options of some library. """

        validate = Option(bool, True)
        """ Whether to validate arguments to functions and methods. """

        eq_atol = Option(float, 1e-8, lambda x: x >= 0)
        """ Absolute tolerance used for equality comparisons."""

        scaling = Option(
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

It is possible to set multiple options simultaneously using the `set <https://optmanage.readthedocs.io/en/latest/api/optmanage.manager.html#optmanage.manager.OptionManager.set>`_ method of the ``options`` object:

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

All options can be reset to their default values by using the `OptionManager.reset <https://optmanage.readthedocs.io/en/latest/api/optmanage.manager.html#optmanage.manager.OptionManager.reset>`_ method of the ``options`` object:

.. code-block:: python

    options.set(validate=False, eq_atol=1e-3)
    print(options.validate) # False
    print(options.eq_atol)  # 0.001
    options.reset()
    print(options.validate) # True
    print(options.eq_atol)  # 0.00000001

An individual option can be reset to its default value by using the `Option.reset <https://optmanage.readthedocs.io/en/latest/api/optmanage.option.html#optmanage.option.Option.reset>`_ method of the `Option <https://optmanage.readthedocs.io/en/latest/api/optmanage.option.html#option>`_ object, accessed from the option manager class:

.. code-block:: python

    options.set(validate=False, eq_atol=1e-3)
    print(options.validate) # False
    print(options.eq_atol)  # 0.001
    MyOptions.eq_atol.reset(options) # resets 'eq_atol' on the 'options' object
    print(options.validate) # True
    print(options.eq_atol)  # 0.001


API
---

Full documentation is available at https://optmanage.readthedocs.io/


Contributing
------------

This project is currently in private development. Public contribution guidelines are available at `<CONTRIBUTING.md>`_.


License
-------

`MIT © Hashberg Ltd. <LICENSE>`_
