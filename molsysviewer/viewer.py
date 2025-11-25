from __future__ import annotations

from typing import Any

import molsysmt as msm
import numpy as np

from ipywidgets.embed import embed_minimal_html

from ._private.variables import is_all
from .widget import MolSysViewerWidget
from .loaders import load_from_molsysmt as _load_from_molsysmt
from .shapes import ShapesManager


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
            self,
            molecular_system=molecular_system,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            label=label,
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

    def write_html(self, output_filename: str, *, title: str = "MolSysViewer") -> None:
        """Export this viewer widget to a standalone HTML file (for docs embedding)."""
        embed_minimal_html(output_filename, views=[self.widget], title=title, drop_defaults=True)

    # --- Tests de vida / demos ---

    def _life_test(self) -> None:
        """Test de vida -> carga una PDB de ejemplo en Mol*."""
        from .loader import load_pdb_id
        load_pdb_id(self, pdb_id="1crn", label="Demo: 1CRN")
        self.show()

    def demo(self) -> None:
        """Test de vida -> carga una PDB de ejemplo en Mol*."""
        self.load(pdb_id="1TCD")
        self.show()
