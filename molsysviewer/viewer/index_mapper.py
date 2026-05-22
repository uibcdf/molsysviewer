# molsysviewer/viewer/index_mapper.py

from __future__ import annotations
from typing import Any
import numpy as np
import molsysmt as msm

class IndexMapper:
    """Helper class to map between original/global indices and local viewer-loaded indices."""

    def __init__(
        self,
        molecular_system: Any,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
    ):
        self.selection = selection
        self.structure_indices = structure_indices
        self.syntax = syntax

        # 1. Atom Indices Mapping
        try:
            original_atoms = msm.select(molecular_system, selection=selection, syntax=syntax)
            if isinstance(original_atoms, np.ndarray):
                self.original_atoms = original_atoms.tolist()
            else:
                self.original_atoms = list(original_atoms)
        except Exception:
            try:
                n_atoms = int(msm.get(molecular_system, element="system", n_atoms=True))
            except Exception:
                n_atoms = 1
            self.original_atoms = list(range(n_atoms))

        self.atom_to_local = {orig: local for local, orig in enumerate(self.original_atoms)}

        # 2. Structure/Frame Indices Mapping
        if structure_indices is None or (isinstance(structure_indices, str) and structure_indices == "all"):
            try:
                n_structures = int(msm.get(molecular_system, element="system", n_structures=True))
            except Exception:
                try:
                    n_structures = int(msm.get(molecular_system, element="structure", n_structures=True))
                except Exception:
                    n_structures = 1
            self.original_structures = list(range(n_structures))
        else:
            if isinstance(structure_indices, np.ndarray):
                self.original_structures = structure_indices.tolist()
            elif isinstance(structure_indices, (list, tuple, range)):
                self.original_structures = list(structure_indices)
            else:
                self.original_structures = [int(structure_indices)]

        self.structure_to_local = {orig: local for local, orig in enumerate(self.original_structures)}

    def to_local_atom(self, original_index: int | None) -> int | None:
        if original_index is None:
            return None
        return self.atom_to_local.get(int(original_index))

    def to_local_atoms(self, original_indices: Any) -> Any:
        if original_indices is None:
            return None
        if isinstance(original_indices, (int, np.integer)):
            return self.to_local_atom(int(original_indices))
        if isinstance(original_indices, str):
            return original_indices
        
        try:
            # support lists, arrays, ranges, tuples
            res = []
            for idx in original_indices:
                local_idx = self.to_local_atom(idx)
                if local_idx is not None:
                    res.append(local_idx)
            if isinstance(original_indices, np.ndarray):
                return np.array(res, dtype=original_indices.dtype)
            return res
        except Exception:
            return []

    def to_original_atom(self, local_index: int | None) -> int | None:
        if local_index is None:
            return None
        try:
            return self.original_atoms[int(local_index)]
        except (IndexError, ValueError, TypeError):
            return None

    def to_original_atoms(self, local_indices: Any) -> Any:
        if local_indices is None:
            return None
        if isinstance(local_indices, (int, np.integer)):
            return self.to_original_atom(int(local_indices))
        if isinstance(local_indices, str):
            return local_indices
        
        try:
            res = []
            for idx in local_indices:
                orig_idx = self.to_original_atom(idx)
                if orig_idx is not None:
                    res.append(orig_idx)
            if isinstance(local_indices, np.ndarray):
                return np.array(res, dtype=local_indices.dtype)
            return res
        except Exception:
            return []

    def to_local_structure(self, original_index: int | None) -> int | None:
        if original_index is None:
            return None
        return self.structure_to_local.get(int(original_index))

    def to_local_structures(self, original_indices: Any) -> Any:
        if original_indices is None:
            return None
        if isinstance(original_indices, (int, np.integer)):
            return self.to_local_structure(int(original_indices))
        if isinstance(original_indices, str):
            return original_indices
        
        try:
            res = []
            for idx in original_indices:
                local_idx = self.to_local_structure(idx)
                if local_idx is not None:
                    res.append(local_idx)
            if isinstance(original_indices, np.ndarray):
                return np.array(res, dtype=original_indices.dtype)
            return res
        except Exception:
            return []

    def to_original_structure(self, local_index: int | None) -> int | None:
        if local_index is None:
            return None
        try:
            return self.original_structures[int(local_index)]
        except (IndexError, ValueError, TypeError):
            return None

    def to_original_structures(self, local_indices: Any) -> Any:
        if local_indices is None:
            return None
        if isinstance(local_indices, (int, np.integer)):
            return self.to_original_structure(int(local_indices))
        if isinstance(local_indices, str):
            return local_indices
        
        try:
            res = []
            for idx in local_indices:
                orig_idx = self.to_original_structure(idx)
                if orig_idx is not None:
                    res.append(orig_idx)
            if isinstance(local_indices, np.ndarray):
                return np.array(res, dtype=local_indices.dtype)
            return res
        except Exception:
            return []
