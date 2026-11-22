# SPDX-License-Identifier: LGPL-3.0-or-later

"""Descriptor for the options of option managers."""

# Part of OptManage: a library to create flexible option managers
# Copyright (C) 2023 Hashberg Ltd

# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <https://www.gnu.org/licenses/>.

import builtins
from typing import TYPE_CHECKING, Any, Protocol, Self, final, overload
import typing_validation

if TYPE_CHECKING:
    from .manager import OptionManager


class Validator[T](Protocol):
    """Structural type for option validators."""

    def __call__(self, value: T, /) -> bool | None:
        """Checks whether a value is valid, returning or raising on failure."""
        ...


@final
class Option[T]:
    """Descriptor for an option of an option manager."""

    __type: Any
    """Type of the option."""

    __default: T
    """Default value of the option."""

    __validator: Validator[T] | None
    """Additional validator for the option, if any."""

    __type_check: typing_validation.Validator
    """Runtime type check for the option."""

    __owner: builtins.type[OptionManager] | None
    """Option manager class that owns the option, once bound."""

    __name: str | None
    """Name of the option, once bound."""

    __slots__ = (
        "__type",
        "__default",
        "__validator",
        "__type_check",
        "__owner",
        "__name",
    )

    def __new__(
        cls,
        ty: Any,
        default: T,
        validator: Validator[T] | None = None,
    ) -> Self:
        """
        Creates an option with given type, default value and optional validator.

        :meta public:
        """
        if not typing_validation.can_validate(ty):
            raise TypeError(f"Cannot validate against type {ty!r}.")
        if validator is not None and not callable(validator):
            raise TypeError(f"Expected callable validator, got {validator!r}.")
        option = object.__new__(cls)
        option.__type = ty
        option.__default = default
        option.__validator = validator
        option.__type_check = typing_validation.validator(ty)
        option.__owner = None
        option.__name = None
        option.validate(default)
        return option

    @property
    def type(self) -> Any:
        """Type of the option."""
        return self.__type

    @property
    def default(self) -> T:
        """Default value of the option."""
        return self.__default

    @property
    def validator(self) -> Validator[T] | None:
        """Additional validator for the option, if any."""
        return self.__validator

    @property
    def name(self) -> str:
        """
        Name of the option.

        :raises AttributeError: if the option is not bound to an option manager.
        """
        if (name := self.__name) is None:
            raise AttributeError("Option is not bound to an option manager.")
        return name

    @property
    def owner(self) -> builtins.type[OptionManager]:
        """
        Option manager class that owns the option.

        :raises AttributeError: if the option is not bound to an option manager.
        """
        if (owner := self.__owner) is None:
            raise AttributeError("Option is not bound to an option manager.")
        return owner

    def validate(self, value: T) -> None:
        """
        Validates a value for the option.

        :raises TypeError: if the value does not have the type of the option.
        :raises ValueError: if the value is rejected by the validator.
        """
        self.__type_check(value)
        if (validator := self.__validator) is None:
            return
        try:
            valid = validator(value)
        except Exception as e:
            raise ValueError(self.__invalid_value_message(value)) from e
        if valid is False:
            raise ValueError(self.__invalid_value_message(value))

    def reset(self, manager: OptionManager) -> T:
        """
        Resets the option to its default value, returning its previous value.

        :raises TypeError: if the manager is not an instance of the owner.
        :raises ValueError: if the option has a temporary value.
        """
        owner, name = self.__owner, self.__name
        if owner is None or name is None or not isinstance(manager, owner):
            raise TypeError(f"Option {self.__name!r} does not belong to {manager!r}.")
        old_value: T = manager._reset_values((name,))[name]
        return old_value

    def __set_name__(self, owner: builtins.type, name: str) -> None:
        """
        Binds the option to the option manager class that owns it.

        :meta public:
        """
        from .manager import OptionManager  # pylint: disable=import-outside-toplevel

        if self.__owner is not None:
            raise TypeError(
                f"Option {self.__name!r} of {self.__owner.__name__} cannot be "
                f"bound again as {name!r} of {owner.__name__}."
            )
        if not issubclass(owner, OptionManager):
            raise TypeError(
                f"Option {name!r} cannot be bound to {owner.__name__}, "
                "which is not a subclass of OptionManager."
            )
        self.__owner = owner
        self.__name = name

    @overload
    def __get__(self, instance: None, owner: builtins.type | None = None) -> Self: ...

    @overload
    def __get__(
        self, instance: OptionManager, owner: builtins.type | None = None
    ) -> T: ...

    def __get__(
        self, instance: OptionManager | None, owner: builtins.type | None = None
    ) -> T | Self:
        """
        Returns the current value of the option, or the option itself on the class.

        :meta public:
        """
        if instance is None:
            return self
        value: T = instance._get_value(self.name, self.__default)
        return value

    def __set__(self, instance: OptionManager, value: T) -> None:
        """
        Sets the option to a validated value.

        :raises TypeError: if the value does not have the type of the option.
        :raises ValueError: if the value is rejected by the validator.
        :raises ValueError: if the option has a temporary value.

        :meta public:
        """
        instance._set_values({self.name: value})

    def __repr__(self) -> str:
        if self.__name is None:
            return f"Option({self.__type!r}, {self.__default!r})"
        return f"<Option {self.__name!r} of {self.owner.__name__}>"

    def __invalid_value_message(self, value: Any) -> str:
        if self.__name is None:
            return f"Invalid value for option: {value!r}."
        return f"Invalid value for option {self.__name!r}: {value!r}."
