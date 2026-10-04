from __future__ import annotations

from typing import Any

import molsysmt as msm
from depdigest import dep_digest
from smonitor import signal

from ..._private.argdigest import digest
from ...loaders._composition import _validate_pairing, _validate_renderable
from ...new_view import new_view
from ...viewer import MolSysView


def _unique_tag(tag: str, used_tags: set[str], source_index: int) -> str:
    if tag not in used_tags:
        used_tags.add(tag)
        return tag

    base = f"{tag}__{source_index + 1}"
    candidate = base
    counter = 2
    while candidate in used_tags:
        candidate = f"{base}_{counter}"
        counter += 1
    used_tags.add(candidate)
    return candidate


def _import_view_state(result: MolSysView, source_views: list[MolSysView]) -> None:
    from copy import deepcopy

    from ._scene_transfer import _copy_auxiliary, _transfer_state

    combined = None
    offset = 0
    used = {}
    used_sources = set()
    for source_index, source in enumerate(source_views):
        count = int(source._molsys.get_n_atoms())
        state = _transfer_state(source, result, {i: i + offset for i in range(count)}, merge=True)
        state.setdefault("trajectory_plots", [])
        mappings = {}
        for domain in (
            "regions",
            "layers",
            "shapes",
            "annotations",
            "measurements",
            "selections",
            "sections",
            "trajectory_plots",
        ):
            seen = used.setdefault(domain, set())
            mappings[domain] = {r["tag"]: _unique_tag(r["tag"], seen, source_index) for r in state[domain]}
        # Automatic layer tags follow the renamed object that owns them.
        layer_map = mappings["layers"]
        for domain in ("shapes", "annotations", "measurements"):
            for old, new in mappings[domain].items():
                if old not in layer_map:
                    layer_map[old] = new
        uid_map = {r["uid"]: f"merge_{source_index}_{r['uid']}" for r in state["regions"]}
        source_map = {}
        for record in state.get("sources", {}).get("records", []):
            old_id = record["source_id"]
            if old_id in used_sources:
                from uuid import uuid4

                record["parent_source_id"] = old_id
                record["source_id"] = uuid4().hex
            used_sources.add(record["source_id"])
            source_map[old_id] = record["source_id"]
            old_uid = record.get("region_uid")
            if old_uid is not None:
                record["region_uid"] = uid_map.get(old_uid, f"merge_{source_index}_{old_uid}")
            record["region_tag"] = mappings["regions"].get(record.get("region_tag"), record.get("region_tag"))
        for domain, mapping in mappings.items():
            for record in state[domain]:
                old_tag = record["tag"]
                record["tag"] = mapping[old_tag]
                for field in ("layer", "layer_tag"):
                    if record.get(field) in layer_map:
                        record[field] = layer_map[record[field]]
                options = record.get("options", {})
                if options.get("tag") in mapping:
                    options["tag"] = mapping[options["tag"]]
                if options.get("layer_tag") in layer_map:
                    options["layer_tag"] = layer_map[options["layer_tag"]]
                if domain == "regions":
                    record["uid"] = uid_map[record["uid"]]
                    recipe = record["provenance"]
                    if recipe.get("source_id") in source_map:
                        recipe["source_id"] = source_map[recipe["source_id"]]
                    if source_index:
                        record.pop("show_only", None)
                    for key in ("operands", "of"):
                        value = recipe.get(key)
                        if isinstance(value, list):
                            recipe[key] = [uid_map.get(i, i) for i in value]
                        elif value in uid_map:
                            recipe[key] = uid_map[value]
                    record["order"] += offset
        if combined is None:
            combined = deepcopy(state)
        else:
            for domain in mappings:
                combined[domain].extend(state[domain])
            combined["whole"]["color_layer"].update(state["whole"]["color_layer"])
            combined.setdefault("sources", {"version": 1, "binding": result._source_state_binding(), "records": []})
            combined["sources"]["records"].extend(state.get("sources", {}).get("records", []))
        offset += count
    if combined is not None:
        for index, record in enumerate(combined.get("sources", {}).get("records", [])):
            record["index"] = index
        result.import_state(combined)
        _copy_auxiliary(source_views[0], result)


@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "view"])
@digest()
def merge(
    views: Any,
    *,
    keep_ids: bool = True,
    debug_js: bool | None = None,
    skip_digestion: bool = False,
) -> MolSysView:
    """Return a new view built by merging multiple existing views.

    The merged view uses the first input view as the source of global state
    (whole representation, controls, and last camera snapshot). Regions, layers,
    shapes, and atom visibility from all views are imported. Tag collisions are
    resolved deterministically by suffixing later duplicates with ``__N``.
    """

    source_views = list(views)
    if not source_views:
        raise ValueError("merge requires at least one loaded view.")
    for view in source_views:
        if view._molsys is None:
            raise ValueError("merge requires loaded molecular systems.")
        _validate_renderable(view._molsys)
        _validate_pairing(source_views[0]._molsys, view._molsys, "by_index")
    if any(getattr(view._molsys, "interactions", {}) for view in source_views):
        raise ValueError(
            "Merging named interaction analyses requires a scientific embedding contract; use copy or extract."
        )
    merged = msm.merge(
        [view._molsys for view in source_views],  # noqa: SLF001
        keep_ids=keep_ids,
        to_form="molsysmt.MolSys",
        skip_digestion=True,
    )

    result = new_view(
        merged,
        selection="all",
        structure_indices="all",
        debug_js=debug_js,
        skip_digestion=True,
    )
    _import_view_state(result, source_views)
    return result
