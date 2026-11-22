# SPDX-License-Identifier: LGPL-3.0-or-later

import copy
import gc
import pickle
import weakref
from collections.abc import Mapping
from typing import Any, Literal

import pytest

from optmanage import Option, OptionManager


class MyOptions(OptionManager):
    """Options of some library."""

    validate = Option(bool, True)
    """Whether to validate arguments to functions and methods."""

    eq_atol = Option(float, 1e-08, lambda x: x >= 0)
    """Absolute tolerance used for equality comparisons."""


def test_keys_values_items() -> None:
    options = MyOptions()
    assert list(options.keys()) == ["validate", "eq_atol"]
    assert list(options.values()) == [True, 1e-8]
    assert dict(options.items()) == {"validate": True, "eq_atol": 1e-8}


def test_get_default() -> None:
    options = MyOptions()
    assert options.validate is True
    assert options.eq_atol == 1e-8


def test_attribute_set() -> None:
    options = MyOptions()
    options.validate = False
    assert options.validate is False
    options.eq_atol = 1.5
    assert options.eq_atol == 1.5


def test_attribute_set_failure() -> None:
    options = MyOptions()
    with pytest.raises(TypeError):
        options.validate = 2  # type: ignore[assignment]
    with pytest.raises(ValueError):
        options.eq_atol = -2.5


def test_instances_are_independent() -> None:
    options, other = MyOptions(), MyOptions()
    options.validate = False
    assert other.validate is True


def test_set() -> None:
    options = MyOptions()
    assert options.set(validate=False, eq_atol=1.5) == {
        "validate": True,
        "eq_atol": 1e-8,
    }
    assert options.validate is False
    assert options.eq_atol == 1.5


set_failures: list[tuple[dict[str, Any], type[Exception]]] = [
    ({"validate": 2}, TypeError),
    ({"eq_atol": -2.5}, ValueError),
    ({"validate": 2, "eq_atol": -2.5}, TypeError),
    ({"eq_atol": -2.5, "validate": 2}, ValueError),
    ({"eq_atol": 2.5, "validate": 2}, TypeError),
    ({"validate": False, "eq_atol": -2.5}, ValueError),
    ({"validate": False, "missing": 1}, KeyError),
]


@pytest.mark.parametrize(["kwargs", "error"], set_failures)
def test_set_failure(kwargs: Mapping[str, Any], error: type[Exception]) -> None:
    options = MyOptions()
    with pytest.raises(error):
        options.set(**kwargs)
    assert options.validate is True and options.eq_atol == 1e-8


def test_option_reset() -> None:
    options = MyOptions()
    options.validate = False
    assert MyOptions.validate.reset(options) is False
    assert options.validate is True
    assert MyOptions.validate.reset(options) is True


def test_reset() -> None:
    options = MyOptions()
    options.validate = False
    options.eq_atol = 1.5
    assert options.reset() == {"validate": False, "eq_atol": 1.5}
    assert options.validate is True
    assert options.eq_atol == 1e-8


def test_temporary_set() -> None:
    options = MyOptions()
    options.eq_atol = 0.5
    with options(validate=False, eq_atol=1.5):
        assert options.validate is False
        assert options.eq_atol == 1.5
        with options(eq_atol=2.5):
            assert options.eq_atol == 2.5
        assert options.eq_atol == 1.5
    assert options.validate is True
    assert options.eq_atol == 0.5
    assert MyOptions.validate.reset(options) is True


def test_temporary_set_restored_on_exception() -> None:
    options = MyOptions()
    with pytest.raises(RuntimeError):
        with options(validate=False):
            raise RuntimeError()
    assert options.validate is True


@pytest.mark.parametrize(["kwargs", "error"], set_failures)
def test_temporary_set_failure(
    kwargs: Mapping[str, Any], error: type[Exception]
) -> None:
    options = MyOptions()
    with pytest.raises(error):
        with options(**kwargs):
            pass
    assert options.validate is True and options.eq_atol == 1e-8


def test_permanent_changes_refused_during_temporary_set() -> None:
    options = MyOptions()
    with options(validate=False):
        with pytest.raises(ValueError):
            options.validate = True
        with pytest.raises(ValueError):
            options.set(validate=True)
        with pytest.raises(ValueError):
            options["validate"] = True
        with pytest.raises(ValueError):
            MyOptions.validate.reset(options)
        options.eq_atol = 1.5
        with pytest.raises(ValueError):
            options.reset()
        assert options.eq_atol == 1.5
        assert options.validate is False
    assert options.validate is True


def test_item_access() -> None:
    options = MyOptions()
    assert options["validate"] is True
    options["validate"] = False
    assert options["validate"] is False
    with pytest.raises(TypeError):
        options["eq_atol"] = "1.5"


@pytest.mark.parametrize("name", ["missing", "set", "keys", "__class__"])
def test_item_access_to_non_options(name: str) -> None:
    options = MyOptions()
    with pytest.raises(KeyError):
        options[name]
    with pytest.raises(KeyError):
        options[name] = 1


def test_repr() -> None:
    assert repr(MyOptions()) == "MyOptions({'validate': True, 'eq_atol': 1e-08})"


def test_inheritance() -> None:
    class BaseOptions(OptionManager):
        a = Option(int, 1)

    class LeftOptions(BaseOptions):
        b = Option(int, 2)

    class RightOptions(BaseOptions):
        c = Option(int, 3)

    class JointOptions(LeftOptions, RightOptions):
        d = Option(int, 4)

    options = JointOptions()
    assert dict(options.items()) == {"a": 1, "c": 3, "b": 2, "d": 4}
    options.a = 5
    assert options.a == 5
    assert BaseOptions().a == 1


def test_duplicate_option_in_bases() -> None:
    class LeftOptions(OptionManager):
        a = Option(int, 1)

    class RightOptions(OptionManager):
        a = Option(int, 2)

    with pytest.raises(TypeError):

        class JointOptions(LeftOptions, RightOptions):
            pass


def test_option_redefined_in_subclass() -> None:
    with pytest.raises(TypeError):

        class SubOptions(MyOptions):
            validate = Option(bool, False)


def test_option_overridden_by_attribute() -> None:
    with pytest.raises(TypeError):

        class SubOptions(MyOptions):
            def validate(self) -> None:  # type: ignore[override]
                pass


@pytest.mark.parametrize("name", ["set", "keys", "reset", "_get_value"])
def test_option_overriding_manager_attribute(name: str) -> None:
    with pytest.raises(TypeError):
        type("BadOptions", (OptionManager,), {name: Option(int, 0)})


def test_option_named_self() -> None:
    class SelfOptions(OptionManager):
        self = Option(int, 0)

    options = SelfOptions()
    options.set(self=1)
    with options(self=2):
        assert options.self == 2
    assert options.self == 1


def test_constructor_arguments() -> None:
    with pytest.raises(TypeError):
        MyOptions(1)

    class InitOptions(MyOptions):
        def __init__(self, validate: bool) -> None:
            self.validate = validate

    assert InitOptions(False).validate is False


def test_managers_are_not_leaked() -> None:
    options = MyOptions()
    options.validate = False
    ref = weakref.ref(options)
    del options
    gc.collect()
    assert ref() is None


def test_unhashable_manager() -> None:
    class EqOptions(OptionManager):
        x = Option(int, 0)

        def __eq__(self, other: object) -> bool:
            return isinstance(other, EqOptions)

    options = EqOptions()
    options.x = 1
    assert options.x == 1


def test_copy_and_pickle() -> None:
    options = MyOptions()
    options.eq_atol = 1.5
    with options(validate=False, eq_atol=2.5):
        copied = copy.copy(options)
        pickled = pickle.loads(pickle.dumps(options))
    for other in (copied, pickled):
        assert dict(other.items()) == {"validate": True, "eq_atol": 1.5}
        other.eq_atol = 3.5
    assert options.eq_atol == 1.5


def test_copy_with_instance_attributes() -> None:
    class AttrOptions(MyOptions):
        def __init__(self) -> None:
            self.label = "x"

    options = AttrOptions()
    options.validate = False
    copied = copy.deepcopy(options)
    assert copied.label == "x" and copied.validate is False


def test_getting_started_example() -> None:
    class ExampleOptions(OptionManager):
        """Options of some library."""

        validate = Option(bool, True)
        """Whether to validate arguments to functions and methods."""

        eq_atol = Option(float, 1e-08, lambda x: x >= 0)
        """Absolute tolerance used for equality comparisons."""

        scaling = Option(
            Mapping[Literal["x", "y", "z"], float],
            {"x": 1.0, "y": 2.0, "z": 1.0},
            lambda scaling: all(v >= 0 for v in scaling.values()),
        )
        """Scaling for coordinate axes used in plots."""

    options = ExampleOptions()
    assert options.scaling == {"x": 1.0, "y": 2.0, "z": 1.0}
    options.scaling = {"x": 2.5, "y": 1.5, "z": 1.0}
    with pytest.raises(TypeError):
        options.scaling = {"w": 1.0}
    with pytest.raises(ValueError):
        options.scaling = {"x": -1.0}
    with options(validate=False, eq_atol=1e-3):
        assert options.validate is False
    options.set(validate=False, eq_atol=1e-3)
    MyOptions.eq_atol.reset(MyOptions())
    ExampleOptions.eq_atol.reset(options)
    assert options.eq_atol == 1e-8 and options.validate is False
