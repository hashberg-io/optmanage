"""
    Base class for option managers.
"""

# OptManage: A library to create flexible option managers.
# Copyright (C) 2023 Hashberg Ltd

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, ClassVar, Type
from .option import Option


class OptionManager:
    """
    A base class that can be used to implement flexible option managers,
    supporting options with default values, static type hints, runtime type
    checking, and custom runtime validation logic.

    Subclasses should define options as class attributes,
    using the :class:`Option` descriptor.

    A simple example of an option manager:

    .. code-block:: python

        class MyOptions(OptionManager):
            ''' Options of some library. '''

            validate = Option(bool, True)
            ''' Whether to validate arguments to  functions and methods. '''

            eq_atol = Option(float, 1e-08, lambda x: x >= 0)
            ''' Absolute tolerance used for equality comparisons.'''

            print_prec = Option(int, 3, lambda x: x >= 0)
            ''' Number of decimal digits to be displayed when printing. '''

    Each option is defined as a class attribute of type :class:`Option`,
    passing a default value, a type, and optionally a validator function:

    .. code-block:: python

        validate = Option(bool, True)
        #     option type ^^^^  ^^^^ default value

        print_prec = Option(int, 3, lambda x: x >= 0)
        #        optional validator ^^^^^^^^^^^^^^^^

    The option manager can then be instantiated as usual:

    .. code-block:: python

        options = MyOptions()

    """

    __options: ClassVar[dict[Type[OptionManager], dict[str, Option[Any]]]] = {}

    def __init_subclass__(cls) -> None:
        """
        Hook to create the initial options mapping for a subclass of
        :class:`OptionManager`, by collecting all options from all
        superclasses of ``cls`` which are themselves subclasses of
        :class:`OptionManager`.

        Options declared in ``cls`` are bound subsequently.

        :raises KeyError: If a duplicate option name is found.
        """
        __options = OptionManager.__options
        mro_options_list = [
            __options.get(cls, {}),
            *(__options[base] for base in cls.__mro__[1:] if base in __options),
        ]
        merged_options: dict[str, Option[Any]] = {}
        for options in reversed(mro_options_list):
            for k, opt in options.items():
                prev_opt = merged_options.get(k, None)
                if prev_opt is None:
                    merged_options[k] = opt
                elif prev_opt is not opt:
                    error = (
                        f"Duplicate option name {k!r} for option managers "
                        f"{prev_opt.owner.__name__} and "
                        f"{opt.owner.__name__} in MRO of {cls.__name__}."
                    )
                    raise KeyError(error)
        OptionManager.__options[cls] = merged_options

    @classmethod
    def _bind_option(cls, name: str, option: Option[Any]) -> None:
        """
        Binds an option to this option manager.

        :raises KeyError: If an option with the same name is already bound.
        """
        assert cls is not OptionManager, "Cannot bind option to OptionManager."
        assert option.owner is cls, "Attempting to incorrectly bind option."
        options = OptionManager.__options.setdefault(cls, {})
        if name in options:
            raise KeyError(f"Duplicate option name {name!r}.")
        options[name] = option

    @classmethod
    def _validate_values(cls, **option_values: Any) -> dict[str, Option[Any]]:
        """
        Validates the given option values. See :meth:`Option.validate`.
        """
        cls_options = cls.__options[cls]
        options: dict[str, Option[Any]] = {}
        for k, v in option_values.items():
            (opt := cls_options[k]).validate(v)
            options[k] = opt
        return options

    __slots__ = ("__weakref__",)

    def set(self, **option_values: Any) -> Mapping[str, Any]:
        """
        Sets values for the given options.
        Returns the old values of the options that were set.

        Example usage:

        .. code-block:: python

            options.set(validate=False, print_prec=5)
            # Permanently sets 'validate' and 'print_prec' options.

        For errors, see :meth:`Option.__set__`.
        """
        options = type(self)._validate_values(**option_values)
        return {k: options[k]._set(self, v) for k, v in option_values.items()}

    def keys(self) -> Iterator[str]:
        """Iterator over option names."""
        options = OptionManager.__options[type(self)]
        return iter(options.keys())

    def values(self) -> Iterator[Any]:
        """Iterator over option values."""
        options = OptionManager.__options[type(self)]
        return (opt._get(self) for opt in options.values())

    def items(self) -> Iterator[tuple[str, Any]]:
        """Iterator over option name-value pairs."""
        options = OptionManager.__options[type(self)]
        return ((k, opt._get(self)) for k, opt in options.items())

    def reset(self) -> Mapping[str, Any]:
        """
        Resets all options to their default values.
        Returns the old values for all options.

        Example usage:

        .. code-block:: python

            options.reset()
            # Permanently resets all options to default values.

        For errors, see :meth:`Option.reset`.
        """
        return {
            k: opt.reset(self)
            for k, opt in OptionManager.__options[type(self)].items()
        }

    @contextmanager
    def __call__(self, **option_values: Any) -> Iterator[None]:
        """
        With-context manager to temporarily set option values.

        Example usage:

        .. code-block:: python

            with options(print_prec=5):
                # Sets 'print_prec' to 5 temporarily in this context.
                ...
            # Value of 'print_prec' is restored to its previous value here.

        :meta public:
        """
        options = type(self)._validate_values(**option_values)
        for k, v in option_values.items():
            options[k]._push(self, v)
        try:
            yield
        finally:
            for k in option_values:
                options[k]._pop(self)

    def __getitem__(self, name: str) -> Any:
        """
        Gets the value of the given option.

        :meta public:
        """
        try:
            return getattr(self, name)
        except AttributeError:
            # pylint: disable = raise-missing-from
            raise KeyError(f"Option {name!r} not found.")

    def __setitem__(self, name: str, value: Any) -> None:
        """
        Sets the value of the given option.

        For errors, see :meth:`Option.__set__`.

        :meta public:
        """
        try:
            setattr(self, name, value)
        except AttributeError:
            # pylint: disable = raise-missing-from
            raise KeyError(f"Option {name!r} not found.")

    def __repr__(self) -> str:
        id_str = f"{id(self):#x}"
        options_lines = [f"  {k!r}: {v!r}," for k, v in self.items()]
        lines = ["OptionManager({", *options_lines, "}) at " + id_str]
        return "\n".join(lines)
