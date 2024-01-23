"""
    A library that can be used to implement flexible option managers,
    supporting options with default values, static type hints, runtime type
    checking, and custom runtime validation logic.

    See :class:`~optmanage.manager.OptionManager` for full details.

"""

# A library to create flexible option managers.
# Copyright (C) 2023 Hashberg Ltd

from __future__ import annotations

__version__ = "1.0.0"

from .option import Option
from .manager import OptionManager

__all__ = ("Option", "OptionManager")
