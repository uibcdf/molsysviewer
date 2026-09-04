from __future__ import annotations


from typing import Any

import molsysmt as msm
from smonitor import signal
from .._private.argdigest import digest
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
    def show(
        self,
        *,
        force: bool = False,
        skip_digestion: bool = False,
        viewer_mode: str | None = None,
        controls_mode: str | None = None,
        panel_mode_style: str | None = None,
        height: str | None = None,
    ):
        """Display the widget, the way `pyplot.show()` displays a figure.

        This is the notebook trigger and nothing else. It used to also take a `selection`
        and edit the atom-visibility mask, which is the half `uibcdf/molsysviewer#71`
        removed: what is drawn is decided by the whole and by regions, each of which has
        its own `show()` and `hide()`.

        Returns the widget on the first call, or on any call with `force=True`; `None`
        afterwards, so re-showing in a loop does not stack widgets.
        """
        if viewer_mode is not None or controls_mode is not None or panel_mode_style is not None:
            self._apply_view_modes(
                viewer_mode=viewer_mode,
                controls_mode=controls_mode,
                panel_mode_style=panel_mode_style,
            )
        if height is not None:
            self.widget.layout.height = height

        if force or not self._already_shown:
            self._already_shown = True
            return self.widget

        return None

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
