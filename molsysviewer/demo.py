from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .viewer.core import MolSysView
from dataclasses import dataclass

from .new_view import new_view


@dataclass(frozen=True)
class _DemoSpec:
    key: str
    system_name: str
    resource_filename: str


class DemoCatalog(Mapping[str, "MolSysView"]):
    """Dictionary-like access to built-in demo views.

    Access demos by key:

    >>> import molsysviewer as viewer
    >>> view = viewer.demo["1TCD"]

    Notes
    -----
    - Each access returns a **fresh** `MolSysView` instance (no shared state).
    - Demo systems are sourced from MolSysMT's own system registry
      (``molsysmt.systems``), the ecosystem's single source of truth for
      molecular data. MolSysViewer does not vendor its own copies, so the
      demos never drift out of sync with MolSysMT (e.g. crystal structures
      keep their per-atom ``b_factor`` / ``occupancy``). If a demo needs a
      system MolSysMT does not provide, request it from the MolSysMT team.
    """

    def __init__(self, specs: list[_DemoSpec]):
        self._specs = {spec.key: spec for spec in specs}

    def __getitem__(self, key: str):
        spec = self._specs[key]
        import molsysmt as msm

        demo_system = msm.systems[spec.system_name][spec.resource_filename]
        return new_view(demo_system)

    def __iter__(self) -> Iterator[str]:
        return iter(self._specs)

    def __len__(self) -> int:
        return len(self._specs)

    def __repr__(self) -> str:  # pragma: no cover
        keys = ", ".join(sorted(self._specs))
        return f"DemoCatalog({keys})"


demo = DemoCatalog(
    [
        _DemoSpec("dialanine", "alanine dipeptide", "alanine_dipeptide.h5msm"),
        _DemoSpec("1TCD", "TcTIM", "1tcd.bcif.gz"),
        _DemoSpec("181L", "T4 lysozyme L99A", "181l.bcif.gz"),
        _DemoSpec("pentalanine", "pentalanine", "traj_pentalanine.h5msm"),
        _DemoSpec(
            "chicken_villin_HP35",
            "chicken villin HP35",
            "traj_chicken_villin_HP35_solvated.h5msm",
        ),
    ]
)


__all__ = ["DemoCatalog", "demo"]
