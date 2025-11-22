from __future__ import annotations

from typing import Any

import molsysmt as msm
import numpy as np

from ._private.variables import is_all
from .widget import MolSysViewerWidget
from .loaders import load_from_molsysmt as _load_from_molsysmt
from .shapes import ShapesManager


class MolSysView:
    """Widget de visualización basado en Mol* para sistemas de MolSysMT."""

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
        selection="all",
        structure_indices="all",
        syntax="MolSysMT",
        label: str | None = None,
    ) -> None:
        _load_from_molsysmt(
            self,
            molecular_system=molecular_system,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            label=label,
        )

    def hide(self, selection='all', structure_indices='all', syntax="MolSysMT"):
        """Hide atoms matching the given MolSysMT selection.

        Notes
        -----
        - `structure_indices` is currently ignored for visibility control.
          It only matters at load time when deciding which structures/frames
          are present in `self._molsys`.
        """
        if self.atom_mask is None or self._molsys is None:
            return

        if is_all(selection):
            # Hide everything
            self.atom_mask[:] = False
        else:
            atom_indices = msm.select(self._molsys, selection=selection, syntax=syntax)
            self.atom_mask[atom_indices] = False

        self._update_visibility_in_frontend()

    def show(self, selection='all', structure_indices='all', syntax="MolSysMT", *, force=False):
        """
        Display the MolSysViewer widget the *first time* or whenever force=True.
    
        Parameters
        ----------
        selection : str or sequence of indices, default 'all'
            MolSysMT-style selection used to make atoms visible:
            - 'all' → show all atoms (reset visibility),
            - other → show only the selected atoms (in addition to whatever is already visible).
        structure_indices : str or sequence, default 'all'
            Currently unused for visibility (only meaningful in load()).
        syntax : str, default 'MolSysMT'
            Syntax for the selection language.
        force : bool, default False
            - False → return the widget only the first time this method is called.
            - True  → always return the widget and set _already_shown=True.
    
        Returns
        -------
        The viewer widget if appropriate, otherwise None.
        """
    
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

    def isolate(self, selection='all', structure_indices='all', syntax="MolSysMT"):
        """Show only the atoms in `selection`; hide everything else.

        Notes
        -----
        - If `selection == 'all'` this is equivalent to a visibility reset.
        """
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
        """
        Clear all *decorative* visual elements from the scene, without touching:
    
        - the loaded molecular system,
        - atom visibility or masks,
        - the camera view.
    
        Parameters
        ----------
        shapes : bool, default True
            Remove user-added shapes (spheres, arrows, surfaces, etc.).
        styles : bool, default True
            Remove transient styling or coloring decorations.
        labels : bool, default True
            Remove text labels.
    
        Notes
        -----
        This does not unload or modify the molecular system itself.
        """
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
        """Fully clear the viewer and reset internal state.

        After calling this, a new `load(...)` is required to display a
        molecular system again.

        - removes molecule, shapes, styles and labels on the JS side,
        - resets masks and cached MolSysMT objects on the Python side.
        """
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

    # --- Tests de vida / demos ---

    def demo(self) -> None:
        """Test de vida -> carga una PDB de ejemplo en Mol*."""
        self._send({"op": "test_pdb_id"})
