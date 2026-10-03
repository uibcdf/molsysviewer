"""Viewer entrypoint; importing a leaf utility does not initialize the facade."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import MolSysView

__all__ = ["MolSysView"]


def __getattr__(name):
    if name == "MolSysView":
        from .core import MolSysView

        globals()[name] = MolSysView
        return MolSysView
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
