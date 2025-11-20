from __future__ import annotations

import logging
from typing import Any

import molsysmt as msm
import numpy as np

from molsysmt import pyunitwizard as puw

from ._private.variables import is_all
from .widget import MolSysViewerWidget
from .shapes import ShapesModule


logger = logging.getLogger(__name__)


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
        if self._try_load_native_molsys(label=label):
            return
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

    def _try_load_native_molsys(self, label: str | None = None) -> bool:
        if self._molsys is None:
            return False
        try:
            payload = self._serialize_molsys_payload(self._molsys)
        except Exception as exc:  # pragma: no cover - defensive, MolSysMT internals
            logger.debug("MolSys payload serialization failed: %s", exc, exc_info=True)
            return False
        if payload is None:
            return False
        self._load_molsys_payload(payload, label=label)
        return True

    def _serialize_molsys_payload(self, molsys: Any) -> dict[str, Any] | None:
        n_atoms = msm.get(molsys, element="atom", n_atoms=True)
        if not n_atoms:
            return None

        atom_ids = self._prepare_atom_field(self._safe_atom_get(molsys, atom_id=True), n_atoms, lambda i: i + 1)
        atom_names = self._prepare_atom_field(
            self._safe_atom_get(molsys, atom_name=True), n_atoms, lambda i: f"A{i + 1}"
        )
        residue_ids = self._prepare_atom_field(
            self._first_available(
                [
                    self._safe_atom_get(molsys, group_id=True),
                    self._safe_atom_get(molsys, component_id=True),
                ]
            ),
            n_atoms,
            lambda _i: 1,
        )
        residue_names = self._prepare_atom_field(
            self._first_available(
                [
                    self._safe_atom_get(molsys, group_name=True),
                    self._safe_atom_get(molsys, component_name=True),
                ]
            ),
            n_atoms,
            lambda _i: "RES",
        )
        chain_ids = self._prepare_atom_field(self._safe_atom_get(molsys, chain_id=True), n_atoms, lambda _i: "A")
        entity_ids = self._prepare_atom_field(
            self._first_available(
                [
                    self._safe_atom_get(molsys, entity_id=True),
                    self._safe_atom_get(molsys, molecule_id=True),
                ]
            ),
            n_atoms,
            lambda _i: "1",
        )
        element_symbols = self._prepare_atom_field(
            self._first_available(
                [
                    self._safe_atom_get(molsys, element_symbol=True),
                    self._safe_atom_get(molsys, atom_type=True),
                ]
            ),
            n_atoms,
            lambda _i: "C",
        )
        formal_charges = self._prepare_atom_field(self._safe_atom_get(molsys, formal_charge=True), n_atoms, lambda _i: 0)

        coordinates_quantity = self._safe_atom_get(molsys, coordinates=True, structure_indices="all")
        if coordinates_quantity is None:
            return None
        coordinates_array = self._coordinates_to_angstroms(coordinates_quantity)
        if coordinates_array is None:
            return None

        if coordinates_array.ndim == 2 and coordinates_array.shape[1] == 3:
            coordinates_array = coordinates_array[np.newaxis, ...]
        if coordinates_array.ndim != 3 or coordinates_array.shape[1] != n_atoms:
            return None

        box_lengths = self._safe_structure_get(molsys, box_lengths=True, structure_indices="all")
        box_angles = self._safe_structure_get(molsys, box_angles=True, structure_indices="all")
        lengths_array = self._to_plain_array(box_lengths, to_unit="angstrom")
        angles_array = self._to_plain_array(box_angles, to_unit="degree")

        frames: list[dict[str, Any]] = []
        for frame_index, frame in enumerate(coordinates_array):
            frame_payload: dict[str, Any] = {
                "positions": frame.tolist(),
                "time": frame_index,
            }
            if lengths_array is not None and angles_array is not None:
                if frame_index < len(lengths_array) and frame_index < len(angles_array):
                    cell_lengths = lengths_array[frame_index]
                    cell_angles = angles_array[frame_index]
                    if len(cell_lengths) >= 3 and len(cell_angles) >= 3:
                        frame_payload["cell"] = {
                            "a": float(cell_lengths[0]),
                            "b": float(cell_lengths[1]),
                            "c": float(cell_lengths[2]),
                            "alpha": float(cell_angles[0]),
                            "beta": float(cell_angles[1]),
                            "gamma": float(cell_angles[2]),
                        }
            frames.append(frame_payload)

        bonds_payload = None
        bond_indices = self._first_available(
            [
                self._safe_bond_get(molsys, atom_indices=True),
                self._safe_bond_get(molsys, atoms_indices=True),
                self._safe_bond_get(molsys, atom_index=True),
            ]
        )
        if bond_indices is not None:
            bond_array = np.asarray(bond_indices, dtype=int)
            if bond_array.ndim == 2 and bond_array.shape[1] == 2:
                orders = self._first_available(
                    [
                        self._safe_bond_get(molsys, order=True),
                        self._safe_bond_get(molsys, bond_order=True),
                    ]
                )
                order_array = np.asarray(orders, dtype=int) if orders is not None else None
                bonds_payload = {
                    "indexA": bond_array[:, 0].tolist(),
                    "indexB": bond_array[:, 1].tolist(),
                }
                if order_array is not None and order_array.shape[0] == bond_array.shape[0]:
                    bonds_payload["order"] = order_array.tolist()

        payload: dict[str, Any] = {
            "atoms": {
                "atom_id": atom_ids,
                "atom_name": atom_names,
                "residue_id": residue_ids,
                "residue_name": residue_names,
                "chain_id": chain_ids,
                "entity_id": entity_ids,
                "element_symbol": element_symbols,
                "formal_charge": formal_charges,
            },
            "coordinates": frames,
        }
        if bonds_payload is not None:
            payload["bonds"] = bonds_payload
        return payload

    def _safe_atom_get(self, molsys: Any, **kwargs):
        try:
            return msm.get(molsys, element="atom", **kwargs)
        except Exception:  # pragma: no cover - MolSysMT runtime guard
            logger.debug("MolSys payload: atom get failed for %s", kwargs, exc_info=True)
            return None

    def _safe_structure_get(self, molsys: Any, **kwargs):
        try:
            return msm.get(molsys, element="structure", **kwargs)
        except Exception:  # pragma: no cover
            logger.debug("MolSys payload: structure get failed for %s", kwargs, exc_info=True)
            return None

    def _safe_bond_get(self, molsys: Any, **kwargs):
        try:
            return msm.get(molsys, element="bond", **kwargs)
        except Exception:  # pragma: no cover
            logger.debug("MolSys payload: bond get failed for %s", kwargs, exc_info=True)
            return None

    def _first_available(self, candidates: list[Any | None]) -> Any | None:
        for candidate in candidates:
            if candidate is not None:
                return candidate
        return None

    def _prepare_atom_field(self, values: Any | None, length: int, fallback) -> list[Any]:
        if values is None:
            return [fallback(i) for i in range(length)]
        array = np.asarray(values)
        if array.shape[0] != length:
            return [fallback(i) for i in range(length)]
        return array.tolist()

    def _coordinates_to_angstroms(self, coordinates: Any) -> np.ndarray | None:
        if coordinates is None:
            return None
        try:
            converted = puw.convert(coordinates, to_unit="angstrom")
            values = puw.get_value(converted)
        except Exception:  # pragma: no cover - fallback path
            values = puw.get_value(coordinates) if puw.is_quantity(coordinates) else coordinates
        try:
            return np.asarray(values, dtype=float)
        except Exception:
            logger.debug("MolSys payload: unable to convert coordinates to ndarray", exc_info=True)
            return None

    def _to_plain_array(self, data: Any, to_unit: str | None = None) -> np.ndarray | None:
        if data is None:
            return None
        try:
            if puw.is_quantity(data):
                converted = puw.convert(data, to_unit=to_unit) if to_unit is not None else data
                values = puw.get_value(converted)
            else:
                values = data
            return np.asarray(values)
        except Exception:
            logger.debug("MolSys payload: unable to convert %s to array", to_unit or "values", exc_info=True)
            return None

    def _load_molsys_payload(self, payload: dict[str, Any], *, label: str | None = None) -> None:
        self._send(
            {
                "op": "load_molsys_payload",
                "payload": payload,
                "label": label,
            }
        )

    def _load_pdb_id(self, pdb_id: str, label: str | None = None) -> None:
        """Carga una estructura remota a partir de un PDB ID usando el frontend.
    
        Parameters
        ----------
        pdb_id : str
            Identificador de la estructura en el PDB (por ejemplo, '1aki' o '1AKI').
        label : str, optional
            Etiqueta opcional para identificar la estructura en el viewer.
        """
        if pdb_id is None:
            raise ValueError("pdb_id must be a non-empty string.")
    
        pdb_id_str = str(pdb_id).strip()
        if not pdb_id_str:
            raise ValueError("pdb_id must be a non-empty string.")
    
        # Normalizamos a minúsculas por consistencia, aunque Mol* suele ser case-insensitive.
        pdb_id_str = pdb_id_str.lower()
    
        self._send(
            {
                "op": "load_pdb_id",
                "pdb_id": pdb_id_str,
                "label": label,
            }
        )

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
