# SPDX-License-Identifier: LGPL-3.0-or-later

from collections.abc import Callable, Sequence

import pytest

from optmanage import Option, OptionManager


def test_option_attributes() -> None:
    opt = Option(Sequence[float], [1.5, 2.0])
    assert opt.default == [1.5, 2.0]
    assert opt.type == Sequence[float]
    assert opt.validator is None
    with pytest.raises(AttributeError):
        opt.name
    with pytest.raises(AttributeError):
        opt.owner


def test_option_validator_attribute() -> None:
    validator = lambda x: x >= 0
    opt = Option(float, 1e8, validator)
    assert opt.validator is validator


def test_type_validation() -> None:
    opt = Option(Sequence[float], [1.5, 2.0])
    opt.validate([1e-8])
    with pytest.raises(TypeError):
        opt.validate(1e-8)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        Option(Sequence[float], 1e-8)


def test_validator_returning_false() -> None:
    opt = Option(float, 1e8, lambda x: x >= 0)
    with pytest.raises(ValueError):
        opt.validate(-1.5)
    with pytest.raises(ValueError):
        Option(float, -1.5, lambda x: x >= 0)


def test_validator_returning_none() -> None:
    def validator(x: float) -> None:
        if x < 0:
            raise ValueError("negative")

    opt = Option(float, 1.0, validator)
    opt.validate(2.0)
    with pytest.raises(ValueError) as exc_info:
        opt.validate(-1.0)
    assert isinstance(exc_info.value.__cause__, ValueError)


def test_validator_raising_other_exception() -> None:
    def validator(x: float) -> bool:
        raise RuntimeError("boom")

    with pytest.raises(ValueError) as exc_info:
        Option(float, 1.0, validator)
    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_unsupported_type() -> None:
    with pytest.raises(TypeError):
        Option(Callable[[int], int], lambda x: x)


def test_non_callable_validator() -> None:
    with pytest.raises(TypeError):
        Option(int, 0, 5)  # type: ignore[arg-type]


def test_binding() -> None:
    class MyOptions(OptionManager):
        validate = Option(bool, True)

    opt = MyOptions.validate
    assert opt.name == "validate"
    assert opt.owner is MyOptions


def test_error_message_names_option() -> None:
    class MyOptions(OptionManager):
        eq_atol = Option(float, 1e-8, lambda x: x >= 0)

    with pytest.raises(ValueError, match="'eq_atol'"):
        MyOptions().eq_atol = -1.0


def test_binding_to_non_manager() -> None:
    with pytest.raises(TypeError):

        class NotOptions:
            validate = Option(bool, True)


def test_binding_twice() -> None:
    opt = Option(bool, True)

    class MyOptions(OptionManager):
        validate = opt

    with pytest.raises(TypeError):

        class OtherOptions(OptionManager):
            validate = opt

    assert opt.owner is MyOptions


def test_binding_twice_in_same_class() -> None:
    with pytest.raises(TypeError):

        class MyOptions(OptionManager):
            validate = Option(bool, True)
            check = validate


def test_reset_on_foreign_manager() -> None:
    class MyOptions(OptionManager):
        validate = Option(bool, True)

    class OtherOptions(OptionManager):
        validate = Option(bool, True)

    with pytest.raises(TypeError):
        MyOptions.validate.reset(OtherOptions())


def test_repr() -> None:
    class MyOptions(OptionManager):
        validate = Option(bool, True)

    assert repr(Option(int, 1)) == "Option(<class 'int'>, 1)"
    assert repr(MyOptions.validate) == "<Option 'validate' of MyOptions>"
