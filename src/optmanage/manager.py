# SPDX-License-Identifier: LGPL-3.0-or-later

"""Base class for option managers."""

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

from collections.abc import Collection, Generator, Iterator, Mapping
from contextlib import contextmanager
from typing import Any, ClassVar, Final, Self, final
from .option import Option


@final
class _Unset:
    """Type of the marker for options without an explicitly set value."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "<unset>"


_UNSET: Final = _Unset()
"""Marker for options without an explicitly set value."""

type OptionState = dict[str, Any]
"""Explicitly set option values, by option name."""


class OptionManager:
    """Base class for option managers."""

    __options: ClassVar[Mapping[str, Option[Any]]] = {}
    """Options of the option manager class, by name."""

    __values: dict[str, Any]
    """Explicitly set option values, by option name."""

    __saved: dict[str, list[Any]]
    """Values saved by active temporary contexts, by option name."""

    __slots__ = ("__weakref__", "__values", "__saved")

    def __init_subclass__(cls) -> None:
        """Collects the options of an option manager class."""
        options: dict[str, Option[Any]] = {}
        for base in reversed(cls.__mro__[1:]):
            if not issubclass(base, OptionManager):
                continue
            for name, option in base.__options.items():
                if options.setdefault(name, option) is not option:
                    raise TypeError(
                        f"Option {name!r} of {cls.__name__} is defined by both "
                        f"{options[name].owner.__name__} and "
                        f"{option.owner.__name__}."
                    )
        for name, member in vars(cls).items():
            if name in options and member is not options[name]:
                raise TypeError(
                    f"Attribute {name!r} of {cls.__name__} overrides an option "
                    f"of {options[name].owner.__name__}."
                )
            if not isinstance(member, Option):
                continue
            if hasattr(OptionManager, name):
                raise TypeError(
                    f"Option {name!r} of {cls.__name__} overrides an attribute "
                    "of OptionManager."
                )
            options[name] = member
        cls.__options = options

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        """Creates an option manager with all options at their default values."""
        if (args or kwargs) and cls.__init__ is object.__init__:
            raise TypeError(f"{cls.__name__}() takes no arguments")
        manager = object.__new__(cls)
        manager.__values = {}
        manager.__saved = {}
        return manager

    def keys(self) -> Iterator[str]:
        """Returns an iterator over option names."""
        return iter(type(self).__options)

    def values(self) -> Iterator[Any]:
        """Returns an iterator over option values."""
        return (value for _, value in self.items())

    def items(self) -> Iterator[tuple[str, Any]]:
        """Returns an iterator over option name-value pairs."""
        values = self.__values
        return (
            (name, values.get(name, option.default))
            for name, option in type(self).__options.items()
        )

    def set(self, /, **option_values: Any) -> Mapping[str, Any]:
        """
        Sets the given options, returning their previous values.

        :raises KeyError: if an option does not exist.
        :raises TypeError: if a value does not have the type of its option.
        :raises ValueError: if a value is rejected by the validator of its option.
        :raises ValueError: if an option has a temporary value.
        """
        return self._set_values(option_values)

    def reset(self) -> Mapping[str, Any]:
        """
        Resets all options to their default values, returning their previous values.

        :raises ValueError: if an option has a temporary value.
        """
        return self._reset_values(type(self).__options)

    @contextmanager
    def __call__(self, /, **option_values: Any) -> Generator[None]:
        """
        Sets the given options temporarily, for the duration of a context.

        :raises KeyError: if an option does not exist.
        :raises TypeError: if a value does not have the type of its option.
        :raises ValueError: if a value is rejected by the validator of its option.

        :meta public:
        """
        self.__validate(option_values)
        values, saved = self.__values, self.__saved
        for name, value in option_values.items():
            saved.setdefault(name, []).append(values.get(name, _UNSET))
            values[name] = value
        try:
            yield
        finally:
            for name in option_values:
                stack = saved[name]
                previous = stack.pop()
                if not stack:
                    del saved[name]
                if previous is _UNSET:
                    del values[name]
                else:
                    values[name] = previous

    def __getitem__(self, name: str) -> Any:
        """
        Returns the current value of the given option.

        :raises KeyError: if the option does not exist.

        :meta public:
        """
        option = type(self).__option(name)
        return self.__values.get(name, option.default)

    def __setitem__(self, name: str, value: Any) -> None:
        """
        Sets the given option.

        :raises KeyError: if the option does not exist.
        :raises TypeError: if the value does not have the type of the option.
        :raises ValueError: if the value is rejected by the validator of the option.
        :raises ValueError: if the option has a temporary value.

        :meta public:
        """
        self._set_values({name: value})

    def __repr__(self) -> str:
        return f"{type(self).__name__}({dict(self.items())!r})"

    def __getstate__(self) -> tuple[OptionState, dict[str, Any] | None]:
        """
        Returns the explicitly set permanent option values and instance attributes.

        :meta public:
        """
        values = dict(self.__values)
        for name, stack in self.__saved.items():
            if (permanent := stack[0]) is _UNSET:
                del values[name]
            else:
                values[name] = permanent
        attrs = dict(vars(self)) if hasattr(self, "__dict__") else None
        return values, attrs

    def __setstate__(self, state: tuple[OptionState, dict[str, Any] | None]) -> None:
        """
        Restores the explicitly set option values and instance attributes.

        :meta public:
        """
        values, attrs = state
        self.__values = {}
        self.__saved = {}
        self._set_values(values)
        if attrs is not None:
            vars(self).update(attrs)

    def _get_value(self, name: str, default: Any) -> Any:
        """Returns the current value of the given option."""
        return self.__values.get(name, default)

    def _set_values(self, option_values: Mapping[str, Any]) -> dict[str, Any]:
        """Sets the given options, returning their previous values."""
        options = self.__validate(option_values)
        self.__check_no_temporary_values(option_values, "set")
        values = self.__values
        old_values = {
            name: values.get(name, options[name].default) for name in option_values
        }
        values.update(option_values)
        return old_values

    def _reset_values(self, names: Collection[str]) -> dict[str, Any]:
        """Resets the given options, returning their previous values."""
        options = {name: type(self).__option(name) for name in names}
        self.__check_no_temporary_values(names, "reset")
        values = self.__values
        return {name: values.pop(name, options[name].default) for name in names}

    @classmethod
    def __option(cls, name: str) -> Option[Any]:
        """Returns the option with given name."""
        try:
            return cls.__options[name]
        except KeyError:
            raise KeyError(f"Option {name!r} not found in {cls.__name__}.") from None

    def __validate(self, option_values: Mapping[str, Any]) -> dict[str, Option[Any]]:
        """Validates the given option values, returning the options."""
        options = {name: type(self).__option(name) for name in option_values}
        for name, value in option_values.items():
            options[name].validate(value)
        return options

    def __check_no_temporary_values(self, names: Collection[str], action: str) -> None:
        """Checks that the given options have no temporary values."""
        saved = self.__saved
        for name in names:
            if name in saved:
                raise ValueError(
                    f"Option {name!r} has a temporary value, cannot be "
                    f"permanently {action}."
                )
