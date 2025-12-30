from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from importlib.resources import files

from .new_view import new_view


@dataclass(frozen=True)
class _DemoSpec:
    key: str
    resource_filename: str


class DemoCatalog(Mapping[str, "MolSysView"]):
    """Dictionary-like access to built-in demo views.

    Access demos by key:

    >>> import molsysviewer as viewer
    >>> view = viewer.demo["1TCD"]

    Notes
    -----
    - Each access returns a **fresh** `MolSysView` instance (no shared state).
    - Demo systems are shipped inside the package under `molsysviewer.data.h5msm`.
    """

    def __init__(self, specs: list[_DemoSpec]):
        self._specs = {spec.key: spec for spec in specs}

    def __getitem__(self, key: str):
        spec = self._specs[key]
        demo_system = files("molsysviewer.data.h5msm").joinpath(spec.resource_filename)
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
        _DemoSpec("dialanine", "alanine_dipeptide.h5msm"),
        _DemoSpec("1TCD", "1TCD.h5msm"),
        _DemoSpec("181L", "181L.h5msm"),
        _DemoSpec("pentalanine", "traj_pentalanine.h5msm"),
        _DemoSpec("chicken_villin_HP35", "traj_chicken_villin_HP35_solvated.h5msm"),
    ]
)


__all__ = ["DemoCatalog", "demo"]

