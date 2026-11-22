# optmanage

[![Python versions](https://img.shields.io/badge/python-3.15+-green.svg)](https://docs.python.org/3.15/)
[![PyPI version](https://img.shields.io/pypi/v/optmanage.svg)](https://pypi.python.org/pypi/optmanage/)
[![PyPI status](https://img.shields.io/pypi/status/optmanage.svg)](https://pypi.python.org/pypi/optmanage/)
[![Checked with Mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](https://github.com/python/mypy)
[![Documentation Status](https://readthedocs.org/projects/optmanage/badge/?version=latest)](https://optmanage.readthedocs.io/en/latest/?badge=latest)
[![Python package status](https://github.com/hashberg-io/optmanage/actions/workflows/python.yml/badge.svg)](https://github.com/hashberg-io/optmanage/actions/workflows/python.yml)

Flexible option managers, supporting options with default values, static type hints, runtime type checking via [typing-validation](https://github.com/hashberg-io/typing-validation), and custom runtime validation logic: options are declared as class attributes of an `OptionManager` subclass, and can be set individually, in bulk, or temporarily within a context.

## Install

Install the latest release from [PyPI](https://pypi.org/project/optmanage/):

```console
$ pip install --upgrade optmanage
```

The library requires Python 3.15 or later.

## Usage

Custom option manager classes are created by subclassing `OptionManager` and using the `Option` descriptor to define options.
Each option takes a type, a default value, and an optional validator function, which signals an invalid value by returning `False` or raising an exception.
Any type supported by typing-validation can be used, including type hints such as `Mapping[Literal["x", "y", "z"], float]`.

```python
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
```

Options are accessed and set like attributes, or by name.
Values of the wrong type raise `TypeError`, and values rejected by the validator raise `ValueError`:

```python
print(options.scaling)  # {'x': 1.0, 'y': 2.0, 'z': 1.0}
options.scaling = {"x": 2.5, "y": 1.5, "z": 1.0}
options["eq_atol"] = 1e-6
options.eq_atol = -1.0  # ValueError
```

Several options can be set at once with `set`, which validates all values before setting any, and all options can be reset to their defaults with `reset`:

```python
options.set(validate=False, eq_atol=1e-3)
options.reset()
MyOptions.eq_atol.reset(options)  # resets a single option
```

Calling the option manager gives a context manager which sets options temporarily:

```python
with options(validate=False, eq_atol=1e-3):
    print(options.validate)  # False
print(options.validate)  # True
```

Inheritance, copying and pickling, and the behaviour of temporary values under concurrency are covered in the [getting-started guide](https://optmanage.readthedocs.io/en/latest/getting-started.html).

## API

The full API documentation is available at [optmanage.readthedocs.io](https://optmanage.readthedocs.io/).

## Structure

- `src/optmanage/` — the package source; `option.py` defines the `Option` descriptor and the `Validator` protocol, `manager.py` defines `OptionManager`.
- `tests/` — the pytest suite.
- `docs/` — Sphinx documentation sources, built with `autodoc_typehints.py` (see [sphinx-docscripts](https://github.com/hashberg-io/sphinx-docscripts)).
- `pypi-upload.py` — builds the distribution and uploads it to PyPI.

## Contributing

Contribution guidelines are available in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[LGPL-3.0-or-later](LICENSE) © Hashberg Ltd.
