# pylint: disable = missing-docstring

from __future__ import annotations
from collections.abc import Mapping
from typing import Any, Literal, Type

import pytest

from optmanage.manager import OptionManager
from optmanage.option import Option


def test_init() -> None:
    class MyOptions(OptionManager):
        validate = Option(True, bool)
        eq_atol = Option(1e-08, float, lambda x: x >= 0)
    options = MyOptions()
    keys = ["validate", "eq_atol"]
    values = [True, 1e-8]
    items = dict(zip(keys, values))
    assert list(options.keys()) == keys
    assert list(options.values()) == values
    assert dict(options.items()) == items

def test_get_default() -> None:
    class MyOptions(OptionManager):
        validate = Option(True, bool)
        eq_atol = Option(1e-8, float, lambda x: x >= 0)
    options = MyOptions()
    assert options.validate is True
    assert options.eq_atol == 1e-8

def test_option_set() -> None:
    class MyOptions(OptionManager):
        validate = Option(True, bool)
        eq_atol = Option(1e-8, float, lambda x: x >= 0)
    options = MyOptions()
    options.validate = False
    assert options.validate is False
    options.eq_atol = 1.5
    assert options.eq_atol == 1.5

def test_option_set_failure() -> None:
    class MyOptions(OptionManager):
        validate = Option(True, bool)
        eq_atol = Option(1e-8, float, lambda x: x >= 0)
    options = MyOptions()
    with pytest.raises(TypeError):
        options.validate = 2 # type: ignore
    with pytest.raises(ValueError):
        options.eq_atol = -2.5

def test_set() -> None:
    class MyOptions(OptionManager):
        validate = Option(True, bool)
        eq_atol = Option(1e-8, float, lambda x: x >= 0)
    options = MyOptions()
    options.set(validate=False, eq_atol=1.5)
    assert options.validate is False
    assert options.eq_atol == 1.5

set_failures = [
    (dict(validate=2), TypeError),
    (dict(eq_atol=-2.5), ValueError),
    (dict(validate=2, eq_atol=-2.5), TypeError),
    (dict(eq_atol=-2.5,validate=2), ValueError),
    (dict(eq_atol=2.5,validate=2), TypeError),
    (dict(validate=False, eq_atol=-2.5), ValueError),
]

@pytest.mark.parametrize(["kwargs", "error"], set_failures)
def test_set_failure(kwargs: Mapping[str, Any], error: Type[Exception]) -> None:
    class MyOptions(OptionManager):
        validate = Option(True, bool)
        eq_atol = Option(1e-8, float, lambda x: x >= 0)
    options = MyOptions()
    with pytest.raises(error):
        options.set(**kwargs)
    assert options.validate is True and options.eq_atol == 1e-8

def test_option_reset() -> None:
    class MyOptions(OptionManager):
        validate = Option(True, bool)
        eq_atol = Option(1e-8, float, lambda x: x >= 0)
    options = MyOptions()
    options.validate = False
    MyOptions.validate.reset(options)
    assert options.validate is True
    options.eq_atol = 1.5
    MyOptions.eq_atol.reset(options)
    assert options.eq_atol == 1e-8

def test_reset() -> None:
    class MyOptions(OptionManager):
        validate = Option(True, bool)
        eq_atol = Option(1e-8, float, lambda x: x >= 0)
    options = MyOptions()
    options.validate = False
    options.eq_atol = 1.5
    options.reset()
    assert options.validate is True
    assert options.eq_atol == 1e-8

def test_temp_set() -> None:
    class MyOptions(OptionManager):
        validate = Option(True, bool)
        eq_atol = Option(1e-8, float, lambda x: x >= 0)
    options = MyOptions()
    with options(validate=False, eq_atol=1.5):
        assert options.validate is False
        assert options.eq_atol == 1.5
    assert options.validate is True
    assert options.eq_atol == 1e-8

@pytest.mark.parametrize(["kwargs", "error"], set_failures)
def test_temp_set_failure(kwargs: Mapping[str, Any], error: Type[Exception]) -> None:
    class MyOptions(OptionManager):
        validate = Option(True, bool)
        eq_atol = Option(1e-8, float, lambda x: x >= 0)
    options = MyOptions()
    with pytest.raises(error):
        with options(**kwargs):
            pass
    assert options.validate is True and options.eq_atol == 1e-8


def test_getting_started_example() -> None:
    class MyOptions(OptionManager):
        """ Options of some library. """

        validate = Option(True, bool)
        """ Whether to validate arguments to functions and methods. """

        eq_atol = Option(1e-08, float, lambda x: x >= 0)
        """ Absolute tolerance used for equality comparisons."""

        scaling = Option(
            {"x": 1.0, "y": 2.0, "z": 1.0},
            Mapping[Literal["x", "y", "z"], float],
            lambda scaling: all(v >= 0 for v in scaling.values())
        )
        """ Scaling for coordinate axes used in plots.  """
    options = MyOptions()

