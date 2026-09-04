"""Re-raise a delegated library's argument error as this package's own.

MolSysViewer forwards argument checking to the library that owns the argument —
`uibcdf/molsysviewer#71` measures why: our copies of MolSysMT's attribute digesters accept
exactly the same values theirs do, so the second check is duplication, not safety.

But delegating the *check* must not delegate the *message*. Someone who called
`whole.convert(...)` and reads an error blaming `molsysmt.basic.convert.convert` for an
argument they never passed to MolSysMT has been handed a puzzle instead of a fault. So the
caller is replaced and only the caller.

This is the same decision `_private/argdigest/_quantity.py` already took for PyUnitWizard,
one layer down, and for the same stated reason: one consistent error contract with
argument-named messages.

ArgDigest offers no way to do this from the outside — it computes the caller inside the
decorator as `<owner module>.<function name>`, with no override — so it is done here, on the
way out.
"""

from __future__ import annotations


from .exceptions import ArgumentError


def as_our_argument_error(exc: BaseException, caller: str) -> BaseException:
    """Return `exc` restated as our `ArgumentError`, or `exc` itself if it is not one.

    Returns rather than raises, so the call site keeps `raise ... from exc` visible and the
    original traceback stays chained: the delegated library remains findable by anyone
    debugging, and invisible to anyone merely using.
    """
    extra = getattr(exc, "extra", None)
    if not isinstance(extra, dict):
        # Not a structured error — a conversion failure, a missing file, anything else.
        # Restating those would claim knowledge we do not have.
        return exc

    delegated_caller = extra.get("caller")

    if "argument" in extra:
        # A rejected *value*. Before delegation this was already our `ArgumentError`, a
        # `ValueError`; restating keeps that contract rather than changing it.
        return ArgumentError(
            extra["argument"],
            value=extra.get("value"),
            caller=caller,
        )

    if "argname" in extra and isinstance(delegated_caller, str):
        # An argument the callee does not accept. Before delegation this was already
        # ArgDigest's own error — raised from *our* config, naming our caller — so only
        # the name changes. The type is rebuilt rather than swapped: it is not a
        # `ValueError`, and turning it into one would break `except` clauses that are
        # right today.
        message = extra.get("message")
        if isinstance(message, str) and delegated_caller in message:
            return type(exc)(message=message.replace(delegated_caller, caller, 1))

    return exc
