"""
    Descriptor to define options in an option manager.
"""

# OptManage: A library to create flexible option managers.
# Copyright (C) 2023 Hashberg Ltd

from __future__ import annotations

import sys
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Protocol,
    Type,
    TypeVar,
    overload,
)
from typing_validation import can_validate, validate

if sys.version_info[1] >= 12:
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    from .manager import OptionManager

ValueT = TypeVar("ValueT")
"""
    Invariant type variable for option values (see :class:`Option`).
"""

ValueT_contra = TypeVar("ValueT_contra", contravariant=True)
""" Contravariant type variable for option values (see :class:`Option`). """


class Validator(Protocol[ValueT_contra]):
    """
    Structura type for an option validator.
    """

    def __call__(self, value: ValueT_contra, /) -> bool:
        ...


class Option(Generic[ValueT]):
    """
    Descriptor for an option.
    For usage examples, see :class:`OptionManager`.

    See https://docs.python.org/3/reference/datamodel.html#descriptors
    for a discussion of descriptors in Python.
    """

    __values: dict[OptionManager, ValueT]
    __value_stacks: dict[OptionManager, list[ValueT]]
    __default: ValueT
    __type: Type[ValueT]
    __validator: Validator[ValueT] | None
    __owner: Type[OptionManager]
    __name: str

    __slots__ = (
        "__owner",
        "__name",
        "__values",
        "__value_stacks",
        "__default",
        "__type",
        "__validator",
    )

    def __new__(
        cls,
        default: ValueT,
        ty: Any = None,
        validator: Validator[ValueT] | None = None,
    ) -> Self:
        """
        Creates a new option descriptor.
        For usage examples, see :class:`OptionManager`.

        :param default: The default value for the option.
        :param ty: The type of the option. If not specified, defaults to the
                   type of the default value.
        :param validator: A callable that takes a value and returns whether
                          it is valid for this option. If not specified,
                          defaults to :obj:`None` (no validation)

        :meta public:
        """
        if ty is None:
            ty = type(default)
        elif not can_validate(ty):
            raise TypeError(f"Cannot validate type {ty!r}.")
        if validator is not None and not callable(validator):
            raise TypeError(f"Expected callable validator, got {validator!r}.")
        instance = super().__new__(cls)
        instance.__values = {}
        instance.__value_stacks = {}
        instance.__default = default
        instance.__type = ty
        instance.__validator = validator
        instance.validate(instance.__default)
        return instance

    @property
    def default(self) -> ValueT:
        """
        The default value for this option.
        """
        return self.__default

    @property
    def type(self) -> Type[ValueT]:
        """
        The type of this option.
        """
        return self.__type

    @property
    def validator(self) -> Validator[ValueT] | None:
        """
        The validator for this option, or :obj:`None` if no additional
        validation logic is specified (other than runtime type-checking).
        """
        return self.__validator

    @property
    def name(self) -> str:
        """
        The name of this option.

        :raises AttributeError: if accessed before the option has been
                                bound to an option manager.
        """
        return self.__name

    @property
    def owner(self) -> Type[OptionManager]:
        """
        The owner of this option.

        :raises AttributeError: if accessed before the option has been
                                bound to an option manager.
        """
        return self.__owner

    def validate(self, value: ValueT) -> None:
        """
        Validates a given value for this option:

        - Checks that the value has the correct type.
        - If a validator is specified, checks that the value is valid.
        """
        validate(value, self.__type)
        if (validator := self.__validator) is not None:
            if not validator(value):
                name_str = (
                    f" {self.__name!r}" if hasattr(self, "__name") else ""
                )
                raise ValueError(
                    f"Invalid value for option{name_str}: " f"{value!r}."
                )

    def reset(self, instance: OptionManager) -> ValueT:
        """
        Resets the option to its default value.
        """
        # pylint: disable = import-outside-toplevel
        from .manager import OptionManager

        validate(instance, OptionManager)
        if self._has_temporary_value(instance):
            raise ValueError(
                f"Option {self.__name!r} has a temporary value, "
                "cannot be permanently reset."
            )
        if instance not in (values := self.__values):
            return self.__default
        old_value = values[instance]
        del values[instance]
        return old_value

    def __set_name__(self, owner: Type[OptionManager], name: str) -> None:
        """
        Hook to automatically bind the option to the option manager
        that owns it.

        :meta public:
        """
        self.__owner = owner
        self.__name = name
        owner._bind_option(name, self)

    def __set__(self, instance: OptionManager, value: ValueT) -> None:
        """
        Sets the option to the given value.
        The value is validated before being set.

        :raises TypeError: If the value has the wrong type.
        :raises ValueError: If the value is invalid for this option.
        :raises ValueError: If the option has a temporarily set value.

        :meta public:
        """
        if self._has_temporary_value(instance):
            raise ValueError(
                f"Option {self.__name!r} has a temporary value, "
                "cannot be permanently set."
            )
        self.validate(value)
        self._set(instance, value)

    @overload
    def __get__(
        self, instance: None, _: Type[OptionManager] | None = None
    ) -> Self:
        ...

    @overload
    def __get__(
        self, instance: OptionManager, _: Type[OptionManager] | None = None
    ) -> ValueT:
        ...

    def __get__(
        self,
        instance: OptionManager | None,
        _: Type[OptionManager] | None = None,
    ) -> ValueT | Self:
        """
        Gets the current value for the given option.
        If no value has been set, the default value is returned.

        :meta public:
        """
        if instance is None:
            return self
        return self._get(instance)

    def _get(self, instance: OptionManager) -> ValueT:
        if instance not in (values := self.__values):
            return self.__default
        return values[instance]

    def _set(self, instance: OptionManager, value: ValueT) -> ValueT:
        old_value = self.__values.get(instance, self.__default)
        self.__values[instance] = value
        return old_value

    def _push(self, instance: OptionManager, value: ValueT) -> ValueT:
        old_value = self._get(instance)
        self.__value_stacks.setdefault(instance, []).append(old_value)
        return self._set(instance, value)

    def _pop(self, instance: OptionManager) -> ValueT:
        stack = self.__value_stacks.get(instance, None)
        if not stack:
            raise ValueError(f"Option {self.__name!r} has no temporary value.")
        prev_value = self._set(instance, stack.pop())
        if not stack:
            del self.__value_stacks[instance]
        return prev_value

    def _has_temporary_value(self, instance: OptionManager) -> bool:
        return instance in self.__value_stacks
