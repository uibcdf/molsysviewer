from __future__ import annotations

from importlib.resources import files
from pathlib import Path


class _SystemEntry:
    """Provides path access to a built-in demo system file."""

    def __init__(self, resource_filename: str) -> None:
        self._resource_filename = resource_filename

    @property
    def path(self) -> Path:
        """Absolute path to the system file."""
        return Path(str(files("molsysviewer.data.h5msm").joinpath(self._resource_filename)))

    def __repr__(self) -> str:
        return f"_SystemEntry({self._resource_filename!r})"


class _SystemsCatalog:
    """Attribute-style access to built-in demo system paths.

    Examples
    --------
    >>> import molsysviewer as msv
    >>> path = msv.systems.pentalanine.path
    >>> view = msv.MolSysView()
    >>> view.load(path)
    """

    dialanine = _SystemEntry("alanine_dipeptide.h5msm")
    pentalanine = _SystemEntry("traj_pentalanine.h5msm")
    chicken_villin_HP35 = _SystemEntry("traj_chicken_villin_HP35_solvated.h5msm")
    TCD_1 = _SystemEntry("1TCD.h5msm")
    L_181 = _SystemEntry("181L.h5msm")

    def __repr__(self) -> str:
        names = [k for k in dir(self) if not k.startswith("_")]
        return f"SystemsCatalog({', '.join(names)})"


systems = _SystemsCatalog()

__all__ = ["systems"]
