from __future__ import annotations

from importlib.resources import files
from typing import Any, Callable

from .load import load


def _load_dialanine(**kwargs):
    demo_system = files("molsysviewer.data.h5msm").joinpath("alanine_dipeptide.h5msm")
    return load(demo_system, **kwargs)

def _load_tctim(**kwargs):
    demo_system = files("molsysviewer.data.h5msm").joinpath("1tcd.h5msm")
    return load(demo_system, **kwargs)

def _load_pentalanine(**kwargs):
    demo_system = files("molsysviewer.data.h5msm").joinpath("traj_pentalanine.h5msm")
    return load(demo_system, **kwargs)

def _load_chicken_villin_HP35(**kwargs):
    demo_system = files("molsysviewer.data.h5msm").joinpath("traj_chicken_villin_HP35_solvated.h5msm")
    return load(demo_system, **kwargs)


class _LazyDemo:
    """Lazy proxy so demos can be accessed as attributes (e.g., demo.dialanine.show())."""

    def __init__(self, loader: Callable[[], Any]):
        self._loader = loader
        self._cached: Any | None = None

    def _get(self):
        if self._cached is None:
            self._cached = self._loader()
        return self._cached

    def __getattribute__(self, name: str):
        if name == "__class__":
            cached = object.__getattribute__(self, "_cached")
            return cached.__class__ if cached is not None else type(self)
        return object.__getattribute__(self, name)

    def __getattr__(self, name: str):
        return getattr(self._get(), name)

    def __call__(self, **kwargs):
        if kwargs or self._cached is None:
            return self._loader(**kwargs)
        return self._cached

    @property
    def viewer(self):
        """Return the underlying viewer instance."""
        return self._get()


dialanine = _LazyDemo(_load_dialanine)
pentalanine = _LazyDemo(_load_pentalanine)
tctim = _LazyDemo(_load_tctim)
chicken_villin_HP35 = _LazyDemo(_load_chicken_villin_HP35)


__all__ = ["dialanine", "pentalanine", "tctim", "chicken_villin_HP35"]
