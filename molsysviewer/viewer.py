from __future__ import annotations

import molsysmt as msm
import numpy as np
from typing import Any

from ._private.variables import is_all
from .widget import MolSysViewerWidget
from .shapes import ShapesModule


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
        self.visible_atom_indices = None
        self.visible_structure_indices = None

        self.shapes = ShapesModule(self)

    @property
    def visible_atom_indices(self):
        """Return the indices of currently visible atoms."""
        if self.atom_mask is None:
            return None
        # lista para que sea JSON-serializable sin problemas
        return np.nonzero(self.atom_mask)[0].tolist()

    @property
    def visible_structure_indices(self):
        """Return the indices of currently visible atoms."""
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

    def _ensure_widget(self):
        """Crear el widget una sola vez y devolverlo."""
        if self.widget is None:
            from .widget import MolSysViewerWidget
            self.widget = MolSysViewerWidget()
            self.widget.set_callback(self._receive)
        return self.widget

    def _update_visibility_in_frontend(self):
        if self.atom_mask is None:
            return
        self._send({
            "op": "update_visibility",
            "options": {"visible_atom_indices": self.visible_atom_indices},
        })

    # --- Public loading API ---

    def load(self, molecular_system: Any, selection="all", structure_indices='all', syntax="MolSysMT",
             label: str | None = None) -> None:

        self.molecular_system = molecular_system
        self.selection = selection
        self.structure_indices = structure_indices
        self._molsys = msm.convert(molecular_system, to_form='molsysmt.MolSys',
                                   selection=selection,
                                   structure_indices=structure_indices,
                                   syntax=syntax)
        n_atoms = msm.get(self._molsys, element='atom', n_atoms=True)
        self.atom_mask = np.ones(n_atoms, dtype=bool)
        _temp_pdb_string = msm.convert(self._molsys, to_form='string:pdb')
        self._load_pdb_string(_temp_pdb_string, label=label)

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
            MolSysMT-style selection used to make atoms visible
            (only applied if not 'all').
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
    
        # (1) Apply visibility changes if selection ≠ 'all' and a system is loaded
        if not (is_all(selection) and is_all(structure_indices)):
            if self._molsys is not None and self.atom_mask is not None:
                atom_indices = msm.select(self._molsys, selection=selection, syntax=syntax)
                self.atom_mask[atom_indices] = True
                self._update_visibility_in_frontend()
    
        # (2) Handle first-time or forced visualization
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
            self.reset(what="visibility")
            return

        atom_indices = msm.select(self._molsys, selection=selection, syntax=syntax)
        self.atom_mask[:] = False
        self.atom_mask[atom_indices] = True
        self._update_visibility_in_frontend()

    def reset(self, what="visibility"):
        """
        Reset viewer state.

        Parameters
        ----------
        what : {'visibility', 'view', 'all'}, default 'visibility'
            - 'visibility': reset atom visibility (show all atoms).
            - 'view': reset camera / view.
            - 'all': reset both visibility and view.
        """
        if what not in {"visibility", "view", "all"}:
            raise ValueError(f"Invalid value for `what`: {what}")

        # 1) Reset visibility
        if what in {"visibility", "all"} and self.atom_mask is not None:
            self.atom_mask[:] = True
            self._update_visibility_in_frontend()

        # 2) Reset camera / view
        if what in {"view", "all"}:
            self._send({
                "op": "reset_view",
                "options": {},
            })

        return self._ensure_widget()

    def clear(
        self,
        *,
        shapes: bool = True,
        styles: bool = True,
        labels: bool = True,
    ) -> None:
        """Clear transient visual elements but keep the loaded molecule.

        This is intended to:
        - remove shapes (spheres, arrows, etc.),
        - reset/custom styles,
        - remove labels,

        WITHOUT:
        - unloading the molecular structure,
        - touching `atom_mask`,
        - changing the camera.
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

    def clear_all(self) -> None:
        """Fully clear the viewer and reset internal state.

        After calling this, a new `load(...)` is required to display a
        molecular system again.

        This is more drastic than `clear()`:
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

    # --- Mol* Inner loaders to test ---

    def _load_pdb_string(self, pdb_string: str, *, label: str | None = None) -> None:
        """Cargar una estructura PDB desde un string en el viewer."""
        self._send(
            {
                "op": "load_structure_from_string",
                "format": "pdb",
                "data": pdb_string,
                "label": label,
            },
        )

    def _load_mmcif_string(self, mmcif_string: str, *, label: str | None = None) -> None:
        """Cargar una estructura mmCIF desde un string en el viewer."""
        self._send(
            {
                "op": "load_structure_from_string",
                "format": "mmcif",
                "data": mmcif_string,
                "label": label,
            },
        )

    def _load_from_url(
        self,
        url: str,
        *,
        format: str | None = None,
        label: str | None = None,
    ) -> None:
        """Cargar una estructura remota desde una URL."""
        self._send(
            {
                "op": "load_structure_from_url",
                "url": url,
                "format": format,
                "label": label,
            },
        )
