from __future__ import annotations


import re
from typing import Any, Mapping

import molsysmt as msm
from smonitor import signal
from depdigest import dep_digest

from .._private.arg_digestion import digest
from ..loaders import load_from_molsysmt as _load_from_molsysmt
from .signals import load_signal_extra as _load_signal_extra


class LoadMixin:
    def _reset_load_blocks(self) -> None:
        self._load_blocks = []
        self._empty = True

    @property
    def load_blocks(self) -> list[dict]:
        """Read-only list of load records for every successful load operation."""
        return list(self._load_blocks)

    def _get_input_n_atoms(
        self,
        molecular_system: Any,
        *,
        selection: Any = "all",
        structure_indices: Any = "all",
        syntax: str = "MolSysMT",
    ) -> int:
        return int(
            msm.get(
                molecular_system,
                element="system",
                selection=selection,
                structure_indices=structure_indices,
                syntax=syntax,
                n_atoms=True,
                skip_digestion=True,
            )
        )

    def _input_has_topology(self, molecular_system: Any) -> bool:
        for attribute in ("atom_id", "group_index", "bonded_atom_pairs"):
            try:
                if bool(msm.has_attribute(molecular_system, attribute, include_none=True, skip_digestion=True)):
                    return True
            except Exception:
                continue
        return False

    def _auto_load_mode(
        self,
        molecular_system: Any,
        *,
        selection: Any = "all",
        structure_indices: Any = "all",
        syntax: str = "MolSysMT",
    ) -> str:
        if self._molsys is None:
            return "replace"

        current_n_atoms = self._molsys.get_n_atoms()
        incoming_n_atoms = self._get_input_n_atoms(
            molecular_system,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
        )

        if incoming_n_atoms != current_n_atoms:
            return "add"

        if not self._input_has_topology(molecular_system):
            return "append_structures"

        same_topology = bool(
            msm.compare(
                self._molsys,
                molecular_system,
                selection="all",
                structure_indices="all",
                selection_2=selection,
                structure_indices_2=structure_indices,
                syntax=syntax,
                attribute_type="topological",
                output_type="boolean",
                include_none=True,
                skip_digestion=True,
            )
        )
        return "append_structures" if same_topology else "add"

    def _register_initial_load_block(self, *, n_atoms: int, label: str | None = None) -> None:
        normalized_label = label.strip() if isinstance(label, str) and label.strip() else None
        self._load_blocks = [
            {
                "index": 0,
                "label": normalized_label,
                "n_atoms": int(n_atoms),
                "start": 0,
                "stop": int(n_atoms),
                "region_tag": None,
            }
        ]
        self._empty = False

    def _append_load_block(self, *, n_atoms: int, label: str | None = None) -> dict[str, Any]:
        normalized_label = label.strip() if isinstance(label, str) and label.strip() else None
        start = 0
        if self._load_blocks:
            start = int(self._load_blocks[-1]["stop"])
        block = {
            "index": len(self._load_blocks),
            "label": normalized_label,
            "n_atoms": int(n_atoms),
            "start": start,
            "stop": start + int(n_atoms),
            "region_tag": None,
        }
        self._load_blocks.append(block)
        self._empty = False
        return block

    def _collapse_load_blocks_to_current_whole(self) -> None:
        if self._molsys is None:
            self._reset_load_blocks()
            return
        self._register_initial_load_block(n_atoms=self._molsys.get_n_atoms(), label=self._last_label)

    def _load_region_base_tag(self, block: Mapping[str, Any]) -> str:
        label = block.get("label")
        if isinstance(label, str) and label.strip():
            return self._slugify_region_tag(label)
        load_index = int(block.get("index", 0)) + 1
        return f"Load{load_index}"

    def _ensure_load_regions_after_addition(self) -> None:
        if len(self._load_blocks) < 2:
            return

        used_tags = set(self._regions.keys())
        for block in self._load_blocks:
            if block.get("region_tag") is not None:
                continue
            start = int(block["start"])
            stop = int(block["stop"])
            atom_indices = list(range(start, stop))
            if len(atom_indices) == 0:
                continue
            base_tag = self._load_region_base_tag(block)
            tag = self._unique_region_tag(base_tag, used_tags)
            used_tags.add(tag)
            self.new_region(
                atom_indices=atom_indices,
                tag=tag,
                skip_digestion=True,
            )
            block["region_tag"] = tag

    @dep_digest('molsysmt')
    @signal(tags=["load"], extra_factory=_load_signal_extra)
    @digest()
    def load(
        self,
        molecular_system: Any,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
        label: str | None = None,
        mode: str = "add",
        skip_digestion: bool = False,
    ) -> None:
        """Load a molecular system (MolSysMT-compatible) into the viewer."""
        if mode == "replace":
            self.reset_viewer(skip_digestion=True)
        elif mode == "auto":
            mode = self._auto_load_mode(
                molecular_system,
                selection=selection,
                structure_indices=structure_indices,
                syntax=syntax,
            )

        if self._molsys is None:
            if mode == "append_structures":
                raise ValueError(
                    "No molecular system loaded. Load a topology or full system before calling "
                    "load(..., mode='append_structures')."
                )
            _load_from_molsysmt(
                molecular_system=molecular_system,
                selection=selection,
                structure_indices=structure_indices,
                syntax=syntax,
                label=label,
                skip_digestion=True,
                view=self,
            )
            self._register_initial_load_block(n_atoms=self._molsys.get_n_atoms(), label=label)
            self._last_label = label
            return

        if mode != "add":
            if mode == "append_structures":
                msm.append_structures(
                    self._molsys,
                    molecular_system,
                    selection=selection,
                    structure_indices=structure_indices,
                    syntax=syntax,
                    in_place=True,
                    skip_digestion=True,
                )
                self.apply_system_edit(self._molsys)
                return
            raise ValueError(f"Unsupported load mode: {mode!r}")

        added_molsys = msm.convert(
            molecular_system,
            to_form="molsysmt.MolSys",
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            skip_digestion=True,
        )
        added_n_atoms = int(added_molsys.get_n_atoms())
        visible = self.visible_atom_indices
        msm.add(
            self._molsys,
            added_molsys,
            selection="all",
            structure_indices="all",
            keep_ids=True,
            in_place=True,
            syntax=syntax,
            skip_digestion=True,
        )
        self.apply_system_edit(
            self._molsys,
            label=label,
            visible_atom_indices=visible,
            load_blocks="append",
            appended_n_atoms=added_n_atoms,
        )
        self._ensure_load_regions_after_addition()

    @signal(tags=["config"])
    @digest()
    def load_project_config(
        self,
        path: str,
        *,
        apply_default: bool = False,
        skip_digestion: bool = False,
    ) -> dict[str, Any]:
        """Load a ``_molsysviewer.py`` project config file into this viewer.

        Applies styles (and optionally the default scene style) to this viewer
        and updates the global add-on enable/disable defaults.

        Equivalent to calling ``view.styles.load_project_config(path, ...)``
        and ``molsysviewer.addons.load_project_config(path)`` separately.
        """
        styles_result = self.styles.load_project_config(
            path, apply_default=apply_default, skip_digestion=True
        )
        addons_result = self.addons._host.load_project_config(  # noqa: SLF001
            path, skip_digestion=True
        )
        return {
            "path": styles_result.get("path"),
            "default_scene_style": styles_result.get("default_scene_style"),
            "style_tags": styles_result.get("style_tags", []),
            "applied_default": styles_result.get("applied_default", False),
            "addons_enabled": addons_result.get("addons_enabled", []),
            "addons_disabled": addons_result.get("addons_disabled", []),
        }


LoadMixin.__module__ = "molsysviewer.viewer"
for _name, _value in LoadMixin.__dict__.items():
    if callable(_value):
        try:
            _value.__module__ = "molsysviewer.viewer"
        except Exception:
            pass

