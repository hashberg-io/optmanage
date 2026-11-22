# optmanage

Option managers: `Option` (descriptor) and `Validator` (protocol) in `src/optmanage/option.py`, `OptionManager` (base class) in `src/optmanage/manager.py`, all re-exported from `optmanage`.
Published on PyPI and Read the Docs; licensed LGPL-3.0-or-later since 2.0.0 (1.x was MIT).

## Design

- Option values live on each manager instance, in the private slots `__values` (explicitly set values, by name) and `__saved` (stacks of values displaced by active temporary contexts, with an `_UNSET` marker for "no explicit value").
  This is what makes managers collectable and lets them be unhashable; 1.x kept values in per-option dictionaries keyed by manager, which leaked every manager and required hashability.
- `Option` holds only metadata (type, default, validator, prepared `typing_validation.validator`, owner, name) and delegates storage to the protected `OptionManager._get_value`, `_set_values` and `_reset_values`.
- The options of a class are collected in `__init_subclass__` from the `__options` class attribute of every `OptionManager` base plus the `Option` members of the class body; `__set_name__` only binds owner and name, and runs first.
  Ambiguous definitions raise `TypeError` at class creation (see the Inheritance section of `docs/getting-started.rst` for the list).
- Option names may not shadow attributes of `OptionManager`, which is what keeps `set`, `keys`, the protected helpers and so on safe; `set` and `__call__` take `self` positionally only so that an option may be called `self`.
- `set`, `reset` and `__call__` validate everything before changing anything, so failures are atomic.
  Permanent changes to an option with a temporary value raise `ValueError`.
- Copy and pickle go through `__getstate__`/`__setstate__`, which carry the permanent values only (temporary values are dropped) plus any instance `__dict__`; `__setstate__` revalidates.
- Temporary values are shared across threads and tasks (documented limitation, chosen over contextvars during the 2.0.0 refresh); contexts must exit in reverse order of entry.
- Typo safety: `__setattr__` accepts only options, the internal slots, and names declared by a subclass (in `vars` of a non-`OptionManager` class in the MRO, or in its annotations, read with `annotationlib` in `STRING` format and cached in `__declared` at class creation).
  It raises `AttributeError` with `name` and `obj`, so Python adds "Did you mean" hints; the message has no trailing full stop because Python appends one.
  It is defined under `if not TYPE_CHECKING:` because a visible `__setattr__` makes mypy accept assignment to any attribute, which would lose static typo detection.
- Misuse raises exceptions, never `assert`.

## Conventions

- Python 3.14 and 3.15, both tested locally and in CI; PEP 695 generics, `typing.Self`, one runtime dependency (`typing-validation>=2.2.1`).
- Inside `Option`, the builtin `type` must be written `builtins.type`, because the `type` property shadows it in the class body (for mypy and for lazy annotation evaluation alike).
- Docstrings are one sentence; narrative documentation lives in `docs/getting-started.rst` and `README.md`.
- Docs tooling (`autodoc_typehints.py`, `docs/conf.py`, `docs/make-api.py`) is copied from `hashberg-io/sphinx-docscripts`; Read the Docs builds on Python 3.14, the oldest supported version, so 3.15-only syntax and APIs (such as lazy imports) are off limits.
  Locally, 3.14 runs as `py -V:3.14-arm64`.
  Rebuild with `python make-api.py`, then `sphinx-build -M html . _build`, from `docs/`.

## Checks

- `black --check src tests`, `mypy src tests`, `pytest` (all configured in `pyproject.toml`, also run in CI on 3.14 and 3.15).
  mypy targets 3.14 by configuration; also run `mypy --python-version 3.15 src tests`, and run `pytest` under both interpreters.
- typing-validation 2.2.1 emits a `ByteString` `DeprecationWarning` on import under 3.15; it is fixed upstream on typing-validation's 3.15 branch and is not ours to silence.
