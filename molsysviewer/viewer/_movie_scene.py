"""Movie's serialized scene definition, excluding navigation and owned tracks."""

import hashlib
import json
from copy import deepcopy

# Editor/navigation state is not a rendered molecular-scene definition.
# DOM plots retain their explicit export composition policy.
_EDITOR_FIELDS = {
    "view",
    "active_selection",
    "selections",
    "figure",
    "trajectory_plots",
    "order_high_water_mark",
    "uid_high_water_mark",
    "tag_high_water_marks",
}


def fingerprint(value):
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), allow_nan=False)
    digest = hashlib.sha256()
    for part in encoder.iterencode(value):
        digest.update(part.encode("utf-8"))
    return "sha256:" + digest.hexdigest()


def scene_definition(scene, tracks, collections, *, for_review=False):
    result = deepcopy(scene)
    for key in _EDITOR_FIELDS:
        result.pop(key, None)
    for collection in collections.values():
        result[collection] = {row["tag"]: row for row in result.get(collection, [])}
    if not for_review:
        # Aggregate group flags are derived from member visibility, not another
        # writer of scene content. Retain the independent member definitions.
        for layer in result.get("layers", {}).values():
            layer.pop("hidden", None)
        for interaction in result.get("interactions", {}).values():
            interaction.pop("layer_hidden", None)
    gated_layers = {
        track["target"].get("tag")
        for track in tracks
        if track["target"]["domain"] == "layer" and track["property"] == "visible"
    }
    for domain, collection in collections.items():
        if domain == "layer":
            continue
        for row in result[collection].values():
            layer = row.get("layer_tag") or row.get("options", {}).get("layer_tag") or row.get("layer")
            if layer in gated_layers:
                row.pop("hidden", None)
    result.setdefault("environment", {})
    if "box_display" in result:
        result["box_display"].pop("structure_index", None)
    for track in tracks:
        domain, tag = track["target"]["domain"], track["target"].get("tag")
        prop = track["property"]
        if domain in {"camera", "structure"}:
            continue
        if domain == "scene":
            result["environment"].pop(prop, None)
            continue
        target = result["whole"] if domain == "whole" else result[collections[domain]].get(tag)
        if target is None:
            continue  # Binding validation names missing/replaced targets first.
        if prop == "visible":
            target.pop("visible" if domain == "whole" else "hidden", None)
        elif domain in {"whole", "region"}:
            if prop == "representation":
                target.pop("representation", None)
            elif prop == "color":
                target.setdefault("params", {}).pop("molstar_color_theme", None)
                target["params"].pop("color_scheme", None)
                target.pop("color_scheme", None)
            elif prop == "alpha":
                target.setdefault("params", {}).pop("alpha", None)
        else:
            target.setdefault("style" if domain == "interaction" else "options", {}).pop(prop, None)
    return result


def check_scene(timeline, scene, collections):
    tracks = timeline._data["tracks"]
    baseline = timeline._data["baseline"]["scene"]
    if scene_definition(baseline, tracks, collections) != scene_definition(scene, tracks, collections):
        raise ValueError("Movie scene has untracked changes; reset it or review a rebase before applying the movie.")


def same_data(left, right):
    """Strict JSON structure/bools, accepting numeric JSON 1 and 1.0 alike."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(same_data(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(same_data(a, b) for a, b in zip(left, right, strict=True))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return type(left) is type(right) and left == right


def _summary(value):
    encoded = json.dumps(value, sort_keys=True, allow_nan=False)
    if len(encoded) <= 160:
        return deepcopy(value)
    return {
        "kind": type(value).__name__,
        **({"size": len(value)} if isinstance(value, (dict, list, str)) else {}),
        "sha256": fingerprint(value),
    }


def scene_changes(before, after, collections):
    """One bounded field summary per changed object; never expand atom maps."""
    old = scene_definition(before, [], collections, for_review=True)
    new = scene_definition(after, [], collections, for_review=True)
    domains = {value: key for key, value in collections.items()}
    changes = []

    def compare(domain, tag, a, b):
        if same_data(a, b):
            return
        keys = sorted(set(a or {}) | set(b or {})) if isinstance(a, dict) and isinstance(b, dict) else []
        fields = [key for key in keys if not same_data(a.get(key), b.get(key))]
        changes.append(
            {
                "domain": domain,
                "tag": tag,
                "change": "added" if a is None else "removed" if b is None else "changed",
                "fields": fields,
                "before": _summary(a),
                "after": _summary(b),
            }
        )

    for key in sorted(old.keys() | new.keys()):
        if key in domains:
            for tag in sorted(old.get(key, {}).keys() | new.get(key, {}).keys()):
                compare(domains[key], tag, old.get(key, {}).get(tag), new.get(key, {}).get(tag))
        else:
            compare(key, None, old.get(key), new.get(key))
    return changes
