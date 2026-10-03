from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import molsysmt as msm
from depdigest import dep_digest
from smonitor import signal

from .._private.argdigest import digest
from .._private.scale_budget import check_structure_scale
from ..loaders._composition import (
    _compose_sources,
    _load_record,
    _per_source_selectors,
    _prepare_source,
)
from ..loaders._source_records import (
    _record_atom_runs,
    _remap_source_records,
    _source_atom_indices,
    _source_binding,
    _uncovered_atom_runs,
    _validate_source_state,
)
from ..loaders.load_molsysmt import _commit_molsysmt_load
from .signals import load_signal_extra as _load_signal_extra


class LoadMixin:
    def _reset_load_blocks(self) -> None:
        self._load_blocks = []
        self._load_structure_count = 0
        self._empty = True

    @property
    def load_blocks(self) -> list[dict]:
        """Detached provenance records for independent loaded molecular sources."""
        return self._load_records_snapshot()

    def _load_records_snapshot(self) -> list[dict]:
        records = deepcopy(self._load_blocks)
        for record in records:
            if record.get("region_uid"):
                region = self._region_by_uid(record["region_uid"])
                record["region_tag"] = (
                    region.tag if region is not None and region.provenance.get("source_id") == record.get("source_id")
                    else None
                )
        return records

    def _replace_load_records(self, records) -> None:
        self._load_blocks = records
        self._load_structure_count = 0 if self._molsys is None else int(self._molsys.structures.n_structures)
        self._empty = self._molsys is None

    def _source_state_binding(self):
        if self._molsys is None:
            return None
        structures = self._molsys.structures
        # Public quantity properties may return a fresh wrapper on each read.
        # Announced edits explicitly invalidate the cache, including in-place
        # changes. Unannounced molecular mutations are outside the contract.
        marker = (id(self._molsys), id(structures), int(self._molsys.get_n_atoms()), int(structures.n_structures))
        cached = getattr(self, "_source_binding_memo", None)
        if cached is None or cached[0] != marker:
            cached = (marker, _source_binding(self._molsys, self._structure_identity()))
            self._source_binding_memo = cached
        return deepcopy(cached[1])

    def _export_source_state(self):
        if self._molsys is None or not self._load_blocks:
            return None
        return {"version": 1, "binding": self._source_state_binding(), "records": self.load_blocks}

    def _prepare_source_import(self, state):
        if state is None:
            return None
        records = _validate_source_state(state)
        binding = {key: state["binding"][key] for key in ("n_atoms", "n_structures", "fingerprint")}
        return records if binding == self._source_state_binding() else None

    def _prepare_source_records_edit(self, new_molsys, atom_map, policy, appended, label):
        records = self.load_blocks
        count = int(new_molsys.get_n_atoms())
        prior = sum(record["n_atoms"] for record in records)
        frames = int(new_molsys.structures.n_structures)
        if atom_map is not None:
            from numbers import Integral

            if (not isinstance(atom_map, Mapping)
                    or any(isinstance(i, bool) or not isinstance(i, Integral) or i < 0
                           for pair in atom_map.items() for i in pair)
                    or any(old >= prior or new >= count for old, new in atom_map.items())
                    or len(set(atom_map.values())) != len(atom_map)):
                raise ValueError("atom_index_map must be an injective correspondence within the old/new atom domains.")
        if policy == "collapse" or not records or (atom_map is None and prior != count and policy != "append"):
            return [_load_record(new_molsys, label=label)] if count else []
        if policy == "append" and prior + int(appended) != count:
            raise ValueError("appended_n_atoms must match the growth of the atom domain.")
        records = _remap_source_records(records, atom_map)
        if frames != getattr(self, "_load_structure_count", frames):
            for record in records:
                record["structure_map"] = {"encoding": "runs", "runs": [], "status": "unverified"}
        missing = _uncovered_atom_runs(records, count)
        if missing:
            record = _load_record(new_molsys, index=len(records), label=label,
                                  origin={"form": "molsysmt.MolSys", "reference": None, "kind": "unmapped_edit"})
            _record_atom_runs(record, missing)
            records.append(record)
        return records

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
        record = _load_record(self._molsys, label=label)
        record.update(n_atoms=int(n_atoms), stop=int(n_atoms))
        record["atom_map"]["runs"] = [[0, 0, int(n_atoms)]] if n_atoms else []
        self._load_blocks = [record]
        self._load_structure_count = int(self._molsys.structures.n_structures)
        self._empty = False

    def _append_load_block(self, *, n_atoms: int, label: str | None = None) -> dict[str, Any]:
        normalized_label = label.strip() if isinstance(label, str) and label.strip() else None
        start = 0
        if self._load_blocks:
            start = max(int(record["stop"]) for record in self._load_blocks)
        block = _load_record(self._molsys, index=len(self._load_blocks), offset=start, label=normalized_label)
        block.update(n_atoms=int(n_atoms), stop=start + int(n_atoms))
        block["atom_map"]["runs"] = [[0, start, int(n_atoms)]] if n_atoms else []
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
            if block.get("region_uid") is not None or block.get("region_tag") is not None:
                continue
            atom_indices = _source_atom_indices(block)
            if len(atom_indices) == 0:
                continue
            base_tag = self._load_region_base_tag(block)
            tag = self._unique_region_tag(base_tag, used_tags)
            used_tags.add(tag)
            region = self._new_region_impl(
                atom_indices=atom_indices,
                tag=tag,
                provenance={"kind": "load", "source_id": block.get("source_id"), "frame_dependent": False},
                skip_digestion=True,
            )
            block["region_tag"] = tag
            block["region_uid"] = region.uid

    @dep_digest("molsysmt")
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
        *,
        multiple: bool = False,
        labels: list[str | None] | None = None,
        structure_pairing: str | None = None,
    ) -> None:
        """Load one system, or explicitly combine independent sources.

        ``multiple=True`` interprets the outer list/tuple as independent systems;
        each item may itself contain complementary forms of one system. Flat
        index selectors apply to every source; nested selectors apply per source.
        ``labels`` names the sources, while ``label`` names the composed load.
        Batch modes are ``add`` and ``replace``. Combining several structures
        requires ``structure_pairing='by_index'``; no alignment or broadcast is
        inferred. All sources and composition checks precede scene mutation.

        Source occurrence IDs and compact original/current index maps are exposed
        as detached ``load_blocks`` records. Their region links follow region UID.
        """
        if not isinstance(multiple, bool):
            raise ValueError("multiple must be a boolean.")
        if structure_pairing is not None and structure_pairing != "by_index":
            raise ValueError("structure_pairing must be None or 'by_index'.")
        if mode not in {"add", "replace", "append_structures", "auto"}:
            raise ValueError(f"Unsupported load mode: {mode!r}")
        if multiple:
            if mode not in {"add", "replace"}:
                raise ValueError("Multiple independent sources support only mode='add' or 'replace'.")
            if not isinstance(molecular_system, (list, tuple)) or not molecular_system:
                raise ValueError("multiple=True requires a nonempty list/tuple of sources.")
            sources = list(molecular_system)
            if labels is not None and (
                not isinstance(labels, (list, tuple)) or len(labels) != len(sources)
                or any(value is not None and not isinstance(value, str) for value in labels)
            ):
                raise ValueError("labels must contain one string/None per source.")
            source_labels = [None] * len(sources) if labels is None else list(labels)
            selections = _per_source_selectors(selection, len(sources), "selection")
            frames = _per_source_selectors(structure_indices, len(sources), "structure_indices")
        else:
            if labels is not None:
                raise ValueError("labels requires multiple=True; use label for a single source.")
            sources, source_labels, selections, frames = [molecular_system], [label], [selection], [structure_indices]
        if mode == "auto":
            mode = self._auto_load_mode(
                molecular_system,
                selection=selection,
                structure_indices=structure_indices,
                syntax=syntax,
            )
        if mode == "append_structures":
            if self._molsys is None:
                raise ValueError("Load a system before calling load(..., mode='append_structures').")
            if self.trajectory_plot._cards():
                raise ValueError("Clear trajectory plot cards before appending structures.")
            candidate = msm.append_structures(
                self._molsys, molecular_system, selection=selection,
                structure_indices=structure_indices, syntax=syntax,
                in_place=False, skip_digestion=True,
            )
            records = self.load_blocks
            self.apply_system_edit(candidate)
            # Native append keeps the existing frame prefix. New frames do not
            # acquire fabricated original-frame correspondence for old sources.
            self._replace_load_records(records)
            return

        target = self._molsys if mode == "add" else None
        records = self._load_records_snapshot() if target is not None else []
        offset = int(target.get_n_atoms()) if target is not None else 0
        if target is not None and (not records or sum(record["n_atoms"] for record in records) != offset):
            records = [_load_record(target, label=self._last_label)]
        prepared_sources = []
        for source, source_label, atoms, structures in zip(sources, source_labels, selections, frames):
            prepared, record = _prepare_source(
                source, selection=atoms, structure_indices=structures, syntax=syntax,
                label=source_label, index=len(records), offset=offset,
            )
            prepared_sources.append(prepared)
            records.append(record)
            offset = record["stop"]
        candidate = _compose_sources(target, prepared_sources, structure_pairing)
        if target is not None or len(sources) > 1:
            check_structure_scale(int(candidate.get_n_atoms()), int(candidate.structures.n_structures))
        if target is not None:
            # Preflight existing query recipes on the detached candidate.
            for region in self._regions.values():
                provenance = region.provenance
                if provenance.get("kind") == "query" and not provenance.get("broken"):
                    msm.select(candidate, selection=provenance.get("expression", "all"),
                               syntax=provenance.get("syntax", "MolSysMT"), skip_digestion=True)
            self.apply_system_edit(candidate, label=label, skip_digestion=True)
        else:
            # A replacement clears plots/overlays only after source preparation.
            if mode == "replace":
                self.reset_viewer(skip_digestion=True)
            else:
                self.trajectory_plot._check_structure_axis(candidate.structures.n_structures)
            prepared = prepared_sources[0] if len(sources) == 1 else (
                candidate, candidate, "all", "all", None, None,
            )
            _commit_molsysmt_load(self, prepared, label=label)
            self._last_label = label
        if target is not None or len(sources) > 1:
            # Original indices now belong to a named source, not one global
            # original-system mapper. Runtime indices always address whole.
            self._atom_index_mapper = self._structure_index_mapper = None
            self.selection = self.structure_indices = "all"
        self._replace_load_records(records)
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
        styles_result = self.styles.load_project_config(path, apply_default=apply_default, skip_digestion=True)
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
