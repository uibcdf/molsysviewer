from __future__ import annotations

from typing import Any
import json
import re

import molsysmt as msm
import numpy as np

from ._private.variables import is_all
from .widget import MolSysViewerWidget
from .loaders import load_from_molsysmt as _load_from_molsysmt
from .shapes import ShapesManager

_HTML_MANAGER_VERSION = "1.0.1"
_WIDGETS_BASE_VERSION = "2.0.0"


class MolSysView:
    """Mol* viewer widget with a Python-facing API.

    Provides structure loading, visibility control, shape management, and
    utilities to export static HTML views for documentation or sharing.
    """

    def __init__(self) -> None:
        self.widget = MolSysViewerWidget()

        self.widget.layout.width = "100%"
        self.widget.layout.height = "480px"  # o "600px" si lo prefieres
        self.widget.layout.min_height = "400px"

        self._already_shown = False

        self._ready = False
        self._pending_messages: list[dict] = []
        self._message_history: list[dict] = []

        # Registrar callback para mensajes JS->Python
        def _handle_msg(widget, content, buffers):  # type: ignore[override]
            event = content.get("event")
            if event == "ready":
                self._ready = True
                # En cuanto el frontend esté listo, reenviamos todo
                for msg in self._pending_messages:
                    self.widget.send(msg)
                self._pending_messages.clear()

        self.widget.on_msg(_handle_msg)

        self.molecular_system = None
        self.selection = None
        self.structure_indices = None
        self._molsys = None
        self.atom_mask = None
        self.structure_mask = None

        self.shapes = ShapesManager(self)

    @property
    def visible_atom_indices(self):
        """Return the indices of currently visible atoms."""
        if self.atom_mask is None:
            return None
        # lista para que sea JSON-serializable sin problemas
        return np.nonzero(self.atom_mask)[0].tolist()

    @property
    def visible_structure_indices(self):
        """Return the indices of currently visible structures."""
        if self.structure_mask is None:
            return None
        # lista para que sea JSON-serializable sin problemas
        return np.nonzero(self.structure_mask)[0].tolist()

    # --- util interno ---

    def _send(self, msg: dict) -> None:
        """Enviar un mensaje al frontend o encolarlo si aún no está listo."""
        self._message_history.append(msg)
        if self._ready:
            self.widget.send(msg)
        else:
            self._pending_messages.append(msg)

    def _update_visibility_in_frontend(self):
        if self.atom_mask is None:
            return
        self._send({
            "op": "update_visibility",
            "options": {"visible_atom_indices": self.visible_atom_indices},
        })

    # --- Public loading API ---

    def load(
        self,
        molecular_system: Any,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
        label: str | None = None,
    ) -> None:
        """Load a molecular system (MolSysMT-compatible) into the viewer."""
        _load_from_molsysmt(
            molecular_system=molecular_system,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            label=label,
            view=self,
        )

    def hide(self, selection: str | Any = "all", structure_indices: str | Any = "all", syntax: str = "MolSysMT"):
        """Hide atoms matching the given selection (MolSysMT syntax by default)."""
        if self.atom_mask is None or self._molsys is None:
            return

        if is_all(selection):
            # Hide everything
            self.atom_mask[:] = False
        else:
            atom_indices = msm.select(self._molsys, selection=selection, syntax=syntax)
            self.atom_mask[atom_indices] = False

        self._update_visibility_in_frontend()

    def show(self, selection: str | Any = "all", structure_indices: str | Any = "all", syntax: str = "MolSysMT", *, force: bool = False):
        """Show the widget (first call or if `force=True`) and optionally adjust visibility."""
        # (1) Apply visibility changes if a system is loaded
        if self._molsys is not None and self.atom_mask is not None:
            if is_all(selection) and is_all(structure_indices):
                # Reset visibility: show all atoms
                self.atom_mask[:] = True
                self._update_visibility_in_frontend()
            elif not (is_all(selection) and is_all(structure_indices)):
                # Partial "show": turn on only the requested selection
                atom_indices = msm.select(self._molsys, selection=selection, syntax=syntax)
                self.atom_mask[atom_indices] = True
                self._update_visibility_in_frontend()
    
        # (2) Handle first-time or forced visualisation
        if force or not self._already_shown:
            self._already_shown = True
            return self.widget
    
        # (3) Subsequent calls without force do not return the widget
        return None

    def isolate(self, selection: str | Any = "all", structure_indices: str | Any = "all", syntax: str = "MolSysMT"):
        """Show only the atoms in `selection`; hide everything else (reset if selection == 'all')."""
        if self.atom_mask is None or self._molsys is None:
            return

        if is_all(selection):
            # Isolating "all" → same as reset visibility
            self.atom_mask[:] = True
            self._update_visibility_in_frontend()
            return

        atom_indices = msm.select(self._molsys, selection=selection, syntax=syntax)
        self.atom_mask[:] = False
        self.atom_mask[atom_indices] = True
        self._update_visibility_in_frontend()

    def clear_decorations(
        self,
        *,
        shapes: bool = True,
        styles: bool = True,
        labels: bool = True,
    ) -> None:
        """Clear decorative elements (shapes/styles/labels) without touching the loaded structure or camera."""
        self._send(
            {
                "op": "clear_scene",
                "options": {
                    "shapes": bool(shapes),
                    "styles": bool(styles),
                    "labels": bool(labels),
                },
            }
        )

    def reset_camera(self) -> None:
        """Reset the camera / view in the frontend."""
        self._send({
            "op": "reset_view",
            "options": {},
        })

    def reset_viewer(self) -> None:
        """Fully clear the viewer and reset internal state (requires a new `load(...)`)."""
        # Reset Python-side state
        self.molecular_system = None
        self.selection = None
        self.structure_indices = None
        self._molsys = None
        self.atom_mask = None
        self.structure_mask = None

        # Ask frontend to clear everything (molecule + shapes + view)
        self._send(
            {
                "op": "clear_all",
                "options": {},
            }
        )

    def info(self):
        msm.info(self._molsys)

    # --- Export helpers for docs/notebooks ---

    def write_html(
        self,
        output_filename: str,
        *,
        title: str = "MolSysViewer",
        include_controls: bool = True,
    ) -> None:
        """Export this viewer widget to a standalone HTML file (for docs embedding).

        Parameters
        ----------
        output_filename:
            Path to the HTML file to create.
        title:
            Optional title for the exported HTML page.
        include_controls:
            If ``True`` (default), include the on-canvas control buttons
            (Reset, Fullscreen, background toggle, Spin, Swing) in the exported view.
            Set this to ``False`` if you prefer a minimal viewer without these controls,
            for example when embedding inside another application that already provides
            its own UI.
        """
        # Serialize the message history so the exported HTML can replay all
        # actions (loads/shapes/visibility) without needing a live Python kernel.
        self.widget.initial_messages = self._clean_message_history()
        html = self._build_standalone_html(title=title, include_controls=include_controls)
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(html)

    def _load_anywidget_bundle(self) -> str:
        """Return the JS bundle for anywidget if available to inline in exports."""
        try:
            import anywidget  # type: ignore
        except Exception:
            return ""

        from pathlib import Path

        locations = [
            Path(anywidget.__file__).parent / "nbextension" / "index.js",
            Path(anywidget.__file__).parent / "labextension" / "index.js",
        ]

        sources: list[str] = []
        for path in locations:
            if path.exists():
                try:
                    src = path.read_text(encoding="utf-8")
                    # If this bundle ends with an anonymous AMD define, give it a name
                    # so requirejs can register it when inlined.
                    src = src.replace(
                        'define(["@jupyter-widgets/base"], widget_default);',
                        'define("anywidget-inline", ["@jupyter-widgets/base"], widget_default);\n'
                        'define("anywidget", ["anywidget-inline"], function(m){return m;});',
                    )
                    sources.append(src)
                except Exception:
                    continue

        return "\n".join(sources)

    def _build_standalone_html(self, title: str, include_controls: bool = True) -> str:
        """Create a minimal standalone HTML embedding only this widget."""
        # Ensure initial_messages is in sync before exporting
        self.widget.initial_messages = self._clean_message_history()

        layout_state = self.widget.layout.get_state(drop_defaults=False)
        widget_state = self.widget.get_state(drop_defaults=False)
        # Override toolbar visibility for the exported HTML without mutating
        # the live widget trait in notebooks.
        widget_state["show_controls"] = bool(include_controls)
        widget_state["layout"] = f"IPY_MODEL_{self.widget.layout.model_id}"

        state_json = {
            "version_major": 2,
            "version_minor": 0,
            "state": {
                self.widget.layout.model_id: {
                    "model_name": "LayoutModel",
                    "model_module": "@jupyter-widgets/base",
                    "model_module_version": _WIDGETS_BASE_VERSION,
                    "state": layout_state,
                },
                self.widget.model_id: {
                    "model_name": self.widget._model_name,  # type: ignore[attr-defined]
                    "model_module": self.widget._model_module,  # type: ignore[attr-defined]
                    "model_module_version": self.widget._model_module_version,  # type: ignore[attr-defined]
                    "state": widget_state,
                },
            },
        }
        view_spec = {
            "version_major": 2,
            "version_minor": 0,
            "model_id": self.widget.model_id,
        }

        inline_anywidget = self._load_anywidget_bundle()
        anywidget_script = ""
        if inline_anywidget:
            anywidget_script = (
                "<script>\n"
                "requirejs.config({\n"
                "  map: {'*': {'anywidget': 'anywidget-inline'}},\n"
                f"  paths: {{'@jupyter-widgets/base': 'https://cdn.jsdelivr.net/npm/@jupyter-widgets/base@{_WIDGETS_BASE_VERSION}/dist/index'}}\n"
                "});\n"
                "</script>\n"
                f"<script>\n{inline_anywidget}\n</script>\n"
            )

        template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
</head>
<body>

<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.4/require.min.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@jupyter-widgets/html-manager@{_HTML_MANAGER_VERSION}/dist/embed-amd.js" crossorigin="anonymous"></script>
{anywidget_script}
<script type="application/vnd.jupyter.widget-state+json">
{json.dumps(state_json, separators=(',', ':'))}
</script>
<script type="application/vnd.jupyter.widget-view+json">
{json.dumps(view_spec, separators=(',', ':'))}
</script>

</body>
</html>
"""
        return template

    def _clean_message_history(self) -> list[dict]:
        """Remove redundant messages to keep exports lean."""
        cleaned: list[dict] = []
        for msg in self._message_history:
            if msg.get("op") == "update_visibility":
                opts = msg.get("options") or {}
                vis = opts.get("visible_atom_indices")
                if vis is None or vis == []:
                    continue
                if isinstance(vis, list) and vis == list(range(len(vis))):
                    # Default "show all" is redundant
                    continue
            cleaned.append(msg)
        return cleaned

    # --- Tests de vida / demos ---

    def _life_test(self) -> None:
        """Test de vida -> carga una PDB de ejemplo en Mol*."""
        from .loader import load_pdb_id
        load_pdb_id(pdb_id="1crn", label="Demo: 1CRN", view=self)
        self.show()

    def demo(self) -> None:
        """Test de vida -> carga una PDB de ejemplo en Mol*."""
        self.load(pdb_id="1TCD")
        self.show()
