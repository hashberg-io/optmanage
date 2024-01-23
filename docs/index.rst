
optmanage
=========

Flexible option managers, supporting options with default values, static type hints, runtime type checking, and custom runtime validation logic.

You can install the latest release from `PyPI <https://pypi.org/project/optmanage/>`_ as follows:

.. code-block:: console

    $ pip install --upgrade optmanage

.. code-block:: python

    from optmanage import Option, OptionManager

    class MyOptions(OptionManager):
        """ Options of some library. """

        validate = Option(bool, True)
        """ Whether to validate arguments to functions and methods. """

        eq_atol = Option(float, 1e-8, lambda x: x >= 0)
        """ Absolute tolerance used for equality comparisons."""

    options = MyOptions()
    print(options.validate) # access individual option values
    options.eq_atol = 1e3   # set individual option values
    with options(validate=False):
        ... # temporarily set option values
    options.set(validate=False, eq_atol=1e-5) # set multiple option values

See :doc:`getting-started` for more usage examples.

GitHub repo: https://github.com/hashberg-io/optmanage


.. toctree::
    :maxdepth: 3
    :caption: Contents

    getting-started

.. include:: api-toc.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
