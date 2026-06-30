from __future__ import annotations

__name__ = "molsysviewer.viewer.core"

from typing import Any

import molsysmt as msm
from smonitor import signal
from .._private.arg_digestion import digest
from .._private.smonitor_emit import emit_suppressed_exception
from .._private.variables import is_all


def _ensure_structure_visibility_supported(structure_indices: Any) -> None:
    if is_all(structure_indices):
        return
    raise NotImplementedError(
        "Per-structure visibility is not supported yet; pass structure_indices=\"all\"."
    )


class VisibilityMixin:
    @signal(tags=["visibility"])
    @digest()
    def hide(self, selection: str | Any = "all", structure_indices: str | Any = "all", syntax: str = "MolSysMT", skip_digestion: bool = False):
        """Hide atoms matching the given selection (MolSysMT syntax by default)."""
        _ensure_structure_visibility_supported(structure_indices)
        if self.atom_mask is None or self._molsys is None:
            return

        if is_all(selection):
            # Hide everything: atoms + all reps (global + regions)
            self.atom_mask[:] = False
            self._update_visibility_in_frontend()
            # Hide all representations in the frontend
            self._send({"op": "hide_global", "target": "all"})
        else:
            atom_indices = msm.select(self._molsys, selection=selection, syntax=syntax, skip_digestion=True)
            self.atom_mask[atom_indices] = False

        self._update_visibility_in_frontend()

    @signal(tags=["visibility"])
    @digest()
    def show(self, selection: str | Any = "all", structure_indices: str | Any = "all", syntax: str = "MolSysMT", *, force: bool = False, skip_digestion: bool = False, viewer_mode: str | None = None, controls_mode: str | None = None, panel_mode_style: str | None = None, height: str | None = None):
        """Show the widget (first call or if `force=True`) and optionally adjust visibility or change viewer modes."""
        _ensure_structure_visibility_supported(structure_indices)
        if viewer_mode is not None or controls_mode is not None or panel_mode_style is not None:
            self._apply_view_modes(viewer_mode=viewer_mode, controls_mode=controls_mode, panel_mode_style=panel_mode_style)
        if height is not None:
            self.widget.layout.height = height

        # (1) Apply visibility changes if a system is loaded
        if self._molsys is not None and self.atom_mask is not None:
            if is_all(selection) and is_all(structure_indices):
                # Reset visibility: show all atoms
                self.atom_mask[:] = True
                self._update_visibility_in_frontend()
                # Show all representations in the frontend (global + regions)
                self._send({"op": "show_global", "target": "all"})
                # Re-apply the user's intent about the baseline/global view
                self._send({"op": "hide_global" if self._global_hidden else "show_global", "target": "global"})
            elif not (is_all(selection) and is_all(structure_indices)):
                # Partial "show": turn on only the requested selection
                atom_indices = msm.select(self._molsys, selection=selection, syntax=syntax, skip_digestion=True)
                self.atom_mask[atom_indices] = True
                self._update_visibility_in_frontend()

        # (2) Handle first-time or forced visualisation
        if force or not self._already_shown:
            self._already_shown = True
            return self.widget

        # (3) Subsequent calls without force do not return the widget
        return None

    @signal(tags=["visibility"])
    @digest()
    def isolate(self, selection: str | Any = "all", structure_indices: str | Any = "all", syntax: str = "MolSysMT", skip_digestion: bool = False):
        """Show only the atoms in `selection`; hide everything else (reset if selection == 'all')."""
        _ensure_structure_visibility_supported(structure_indices)
        if self.atom_mask is None or self._molsys is None:
            return

        if is_all(selection):
            # Isolating "all" → same as reset visibility
            self.atom_mask[:] = True
            self._update_visibility_in_frontend()
            return

        atom_indices = msm.select(self._molsys, selection=selection, syntax=syntax, skip_digestion=True)
        self.atom_mask[:] = False
        self.atom_mask[atom_indices] = True
        self._update_visibility_in_frontend()

    @signal(tags=["visibility"])
    @digest()
    def focus_with_fade(self, selection: str | Any = "all", *, fade: float = 0.85,
                        structure_indices: str | Any = "all", syntax: str = "MolSysMT",
                        skip_digestion: bool = False):
        """Soft spotlight: fade everything *outside* `selection` to `fade`
        transparency while keeping the selection fully opaque. Unlike ``isolate``
        it hides nothing — the context stays faintly visible. A generic
        focus-with-fade primitive (e.g. to expose a buried cavity without a
        clipping plane). ``selection`` may be a MolSysMT expression or an explicit
        list of atom indices. Pass ``selection='all'`` or ``fade<=0`` to clear.
        """
        _ensure_structure_visibility_supported(structure_indices)
        if self._molsys is None:
            return

        if (isinstance(selection, str) and is_all(selection)) or fade <= 0:
            self._send({"op": "set_focus_fade",
                        "options": {"focus_atom_indices": None, "fade": 0.0}})
            return

        if isinstance(selection, str):
            atom_indices = msm.select(self._molsys, selection=selection,
                                      syntax=syntax, skip_digestion=True)
        else:
            atom_indices = list(selection)

        self._send({"op": "set_focus_fade",
                    "options": {"focus_atom_indices": [int(i) for i in atom_indices],
                                "fade": float(fade)}})


VisibilityMixin.__module__ = "molsysviewer.viewer"
for _name, _value in VisibilityMixin.__dict__.items():
    if callable(_value):
        try:
            _value.__module__ = "molsysviewer.viewer"
        except Exception as exc:
            emit_suppressed_exception(
                "VisibilityMixin.__module_assignment__",
                exc,
                context={"callable": _name},
            )

