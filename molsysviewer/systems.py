from __future__ import annotations

from pathlib import Path


class _SystemEntry:
    """Provides path access to a built-in demo system file.

    The file is resolved from MolSysMT's own system registry
    (``molsysmt.systems``), so MolSysViewer does not vendor its own copy.
    """

    def __init__(self, system_name: str, resource_filename: str) -> None:
        self._system_name = system_name
        self._resource_filename = resource_filename

    @property
    def path(self) -> Path:
        """Absolute path to the system file inside MolSysMT."""
        import molsysmt as msm

        return Path(str(msm.systems[self._system_name][self._resource_filename]))

    def __repr__(self) -> str:
        return f"_SystemEntry({self._system_name!r}, {self._resource_filename!r})"


class _SystemsCatalog:
    """Attribute-style access to built-in demo system paths.

    Examples
    --------
    >>> import molsysviewer as msv
    >>> path = msv.systems.pentalanine.path
    >>> view = msv.MolSysView()
    >>> view.load(path)
    """

    dialanine = _SystemEntry("alanine dipeptide", "alanine_dipeptide.h5msm")
    pentalanine = _SystemEntry("pentalanine", "traj_pentalanine.h5msm")
    chicken_villin_HP35 = _SystemEntry(
        "chicken villin HP35", "traj_chicken_villin_HP35_solvated.h5msm"
    )
    TCD_1 = _SystemEntry("TcTIM", "1tcd.pdb")
    L_181 = _SystemEntry("T4 lysozyme L99A", "181l.pdb")

    def __repr__(self) -> str:
        names = [k for k in dir(self) if not k.startswith("_")]
        return f"SystemsCatalog({', '.join(names)})"


systems = _SystemsCatalog()

__all__ = ["systems"]
