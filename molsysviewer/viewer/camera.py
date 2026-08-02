from __future__ import annotations

import json
from typing import Any

import molsysmt as msm
from smonitor import signal

from .._private.arg_digestion import digest
from .. import pyunitwizard as puw
from ..regions import Region
from .signals import zoom_signal_extra, camera_snapshot_extra
from .utils import quantity_value_in_unit


class CameraManager:
    """Controls all camera operations for a MolSysView.

    Access via ``view.camera``.

    Positioning
    -----------
    zoom(selection, ...)           Focus on an atom selection.
    focus_selection(selection, ...) Alias for zoom.
    focus_region(region, ...)      Focus on a named region.
    focus_on_object(tag, ...)      Focus on any tagged scene object.
    reset()                        Reset the camera to the default view.

    Snapshot
    --------
    get_snapshot(pretty=False)     Return the last saved camera snapshot.
    set_snapshot(snapshot, ...)    Apply a previously saved snapshot.

    Projection
    ----------
    mode                           ``"perspective"`` or ``"orthographic"``.
    set_mode(mode)                 Switch projection mode.
    """

    def __init__(self, view: Any) -> None:
        self._view = view

    # ── Positioning ───────────────────────────────────────────────────────

    @signal(tags=["camera"], extra_factory=zoom_signal_extra)
    @digest()
    def zoom(
        self,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
        *,
        duration: Any = "250 ms",
        duration_ms: Any | None = None,
        extra_radius: Any = "4.0 angstroms",
        min_radius: Any = "1.0 angstroms",
        skip_digestion: bool = False,
    ) -> None:
        """Focus the camera on the geometric center of a selection of atoms.

        Parameters
        ----------
        selection
            MolSysMT selection string or list of atom indices.
        structure_indices
            Structure indices used when resolving the selection.
        syntax
            Selection syntax understood by MolSysMT.
        duration
            Transition duration (any time unit supported by PyUnitWizard).
        duration_ms
            Backward-compatible alias for *duration*. Overrides *duration* if given.
        extra_radius
            Extra padding added to the selection's bounding sphere.
        min_radius
            Minimum radius to enforce for the camera focus.
        """
        view = self._view
        if view._molsys is None:  # noqa: SLF001
            raise ValueError("No molecular system loaded. Load a system before calling zoom().")

        atom_indices = view.select(
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            skip_digestion=True,
        )
        if not atom_indices:
            raise ValueError("Cannot zoom: empty selection.")

        if duration_ms is not None:
            duration = duration_ms
        duration_ms_value = quantity_value_in_unit(duration, "ms")
        extra_radius_v = round(quantity_value_in_unit(extra_radius, "angstroms"), 6)
        min_radius_v = round(quantity_value_in_unit(min_radius, "angstroms"), 6)

        view._send(  # noqa: SLF001
            {
                "op": "zoom",
                "atom_indices": list(atom_indices),
                "options": {
                    "duration_ms": int(duration_ms_value),
                    "extra_radius": float(extra_radius_v),
                    "min_radius": float(min_radius_v),
                },
            }
        )

    @signal(tags=["camera", "selection"], extra_factory=zoom_signal_extra)
    @digest()
    def focus_selection(
        self,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
        *,
        duration: Any = "250 ms",
        duration_ms: Any | None = None,
        extra_radius: Any = "4.0 angstroms",
        min_radius: Any = "1.0 angstroms",
        skip_digestion: bool = False,
    ) -> None:
        """Focus the camera on a selection of atoms (alias for :meth:`zoom`)."""
        self.zoom(
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            duration=duration,
            duration_ms=duration_ms,
            extra_radius=extra_radius,
            min_radius=min_radius,
            skip_digestion=True,
        )

    @signal(tags=["camera", "region"])
    @digest()
    def focus_region(
        self,
        region: str | Region,
        *,
        duration: Any = "250 ms",
        duration_ms: Any | None = None,
        extra_radius: Any = "4.0 angstroms",
        min_radius: Any = "1.0 angstroms",
        skip_digestion: bool = False,
    ) -> None:
        """Focus the camera on a region identified by tag or Region object."""
        if isinstance(region, str):
            target = self._view._regions.get(region)  # noqa: SLF001
            if target is None:
                raise KeyError(f"Unknown region tag: {region!r}")
        elif isinstance(region, Region):
            target = region
        else:
            raise TypeError("region must be a region tag or Region instance.")

        if target.atom_indices is not None:
            selection: Any = list(target.atom_indices)
            syntax = "MolSysMT"
        else:
            selection = target.selection
            syntax = "MolSysMT"

        self.zoom(
            selection=selection,
            syntax=syntax,
            duration=duration,
            duration_ms=duration_ms,
            extra_radius=extra_radius,
            min_radius=min_radius,
            skip_digestion=True,
        )

    @signal(tags=["camera"])
    @digest()
    def focus_on_object(
        self,
        tag: str,
        *,
        kind: str | None = None,
        duration_ms: int = 250,
        extra_radius: float = 0.5,
        skip_digestion: bool = False,
    ) -> None:
        """Center the camera on a tagged scene object (shape, measurement, region, or annotation).

        Dispatches to the object's own ``focus()`` method when available,
        or to :meth:`focus_region` for regions.

        Parameters
        ----------
        tag
            Tag of the scene object to focus on.
        duration_ms
            Camera transition duration in milliseconds.
        extra_radius
            Extra padding around the object's bounding sphere (nm).
        """
        view = self._view  # noqa: SLF001
        if kind == "region" or (kind is None and tag in view._regions):  # noqa: SLF001
            if kind is None:
                scene_matches = [key for key in view._scene_objects if key[1] == tag]  # noqa: SLF001
                if scene_matches:
                    raise ValueError(f"Ambiguous object tag {tag!r}; pass kind explicitly.")
            if tag not in view._regions:  # noqa: SLF001
                raise KeyError(f"Unknown region tag: {tag!r}")
            self.focus_region(
                view._regions[tag],  # noqa: SLF001
                duration_ms=duration_ms,
                extra_radius=f"{quantity_value_in_unit(extra_radius, 'angstroms')} angstroms",
                skip_digestion=True,
            )
            return

        if kind is None:
            matches = [obj for (_object_kind, object_tag), obj in view._scene_objects.items() if object_tag == tag]  # noqa: SLF001
            if len(matches) > 1:
                raise ValueError(f"Ambiguous object tag {tag!r}; pass kind explicitly.")
            obj = matches[0] if matches else None
        else:
            obj = view._scene_objects.get((kind, tag))  # noqa: SLF001
        if obj is None:
            raise KeyError(f"Unknown object tag: {tag!r}")
        if not hasattr(obj, "focus"):
            raise NotImplementedError(
                f"Objects of kind {getattr(obj, 'kind', '?')!r} do not support focus()."
            )
        obj.focus(duration_ms=duration_ms, extra_radius=extra_radius)

    @signal(tags=["camera"])
    @digest()
    def reset(self, skip_digestion: bool = False) -> None:
        """Reset the camera to the default view."""
        self._view._send({"op": "reset_view", "options": {}})  # noqa: SLF001

    # ── Snapshot ──────────────────────────────────────────────────────────

    @signal(tags=["camera"], extra_factory=lambda args, kwargs: {
        "pretty": args[1] if len(args) > 1 else kwargs.get("pretty", False)
    })
    @digest()
    def get_snapshot(self, *, pretty: bool = False, skip_digestion: bool = False) -> dict | str | None:
        """Return the last camera snapshot received from the frontend.

        Parameters
        ----------
        pretty
            If ``True``, return a formatted JSON string instead of a dict.
        """
        snap = self._view._last_camera_snapshot  # noqa: SLF001
        if snap is None:
            return None
        if not pretty:
            return dict(snap)
        return json.dumps(snap, indent=2, sort_keys=True)

    @signal(tags=["camera"], extra_factory=camera_snapshot_extra)
    @digest()
    def set_snapshot(
        self,
        snapshot: dict,
        *,
        duration_ms: int = 0,
        skip_digestion: bool = False,
    ) -> None:
        """Apply a previously saved camera snapshot.

        Parameters
        ----------
        snapshot
            Camera snapshot dict (Mol* format).
        duration_ms
            Transition duration in milliseconds.
        """
        if not snapshot:
            return
        duration_value = (
            int(puw.get_value(duration_ms, to_unit="ms"))
            if puw.is_quantity(duration_ms)
            else int(duration_ms)
        )
        self._view._last_camera_snapshot = dict(snapshot)  # noqa: SLF001
        self._view._send(  # noqa: SLF001
            {
                "op": "set_camera_snapshot",
                "snapshot": snapshot,
                "duration_ms": duration_value,
            }
        )

    # ── Projection mode ───────────────────────────────────────────────────

    @property
    def mode(self) -> str | None:
        """Current projection mode: ``"perspective"`` or ``"orthographic"``.

        Returns ``None`` if no snapshot has been received yet.
        """
        snap = self._view._last_camera_snapshot  # noqa: SLF001
        if snap is None:
            return None
        return snap.get("camera", {}).get("mode")

    @signal(tags=["camera"])
    @digest()
    def set_mode(self, mode: str, skip_digestion: bool = False) -> None:
        """Switch camera projection mode.

        Parameters
        ----------
        mode
            ``"perspective"`` or ``"orthographic"``.
        """
        mode = str(mode).lower()
        if mode not in ("perspective", "orthographic"):
            raise ValueError(f"mode must be 'perspective' or 'orthographic', got {mode!r}.")
        self._view._send({"op": "set_camera_mode", "mode": mode})  # noqa: SLF001


__all__ = ["CameraManager"]
