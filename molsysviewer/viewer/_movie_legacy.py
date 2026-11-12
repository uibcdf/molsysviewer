"""Compile the admitted legacy profile without changing its sampling semantics."""

import math
from copy import deepcopy

from ._movie_timeline import _EASING, _MAX_SAFE_INTEGER, _camera, _tag, _time

# A serialized-event budget, not an assertion about universal renderer RAM.
_MAX_STRUCTURE_EVENTS = 100_000


def _fraction(at, left, right, easing):
    fraction = max(0.0, min(1.0, (at - left) / (right - left)))
    # Match the legacy renderer's operation order, including outgoing easing.
    if easing == "ease-in":
        return fraction * fraction
    if easing == "ease-out":
        return 1 - (1 - fraction) * (1 - fraction)
    if easing == "ease-in-out":
        return 2 * fraction * fraction if fraction < 0.5 else 1 - 2 * (1 - fraction) * (1 - fraction)
    return fraction


def _rounded_structure(at, left, right):
    fraction = _fraction(at, left["time_ms"], right["time_ms"], left["easing"])
    a, b = left["structure_index"], right["structure_index"]
    value = a + (b - a) * fraction
    integer = math.floor(value)
    # floor(value + .5) can change an already integral large binary64 value.
    # Legacy Math.round chooses the upper integer at an exact positive tie.
    return integer + int(value - integer >= 0.5)


def structure_events(keyframes):
    """Find the first representable timestamp of each actual rounded change."""
    estimate = 1 + sum(abs(b["structure_index"] - a["structure_index"]) for a, b in zip(keyframes, keyframes[1:]))
    if estimate > _MAX_STRUCTURE_EVENTS:
        return None
    events = [{"time_ms": 0.0, "value": keyframes[0]["structure_index"]}]
    for left, right in zip(keyframes, keyframes[1:]):
        a, b = left["structure_index"], right["structure_index"]
        if a == b:
            continue
        step = 1 if b > a else -1
        for value in range(a + step, b + step, step):
            low, high = left["time_ms"], right["time_ms"]
            # Inclusive step keys must account for descending ties and for
            # easing/IEEE-754 rounding, not just a symbolic half-integer time.
            while math.nextafter(low, high) < high:
                middle = low + (high - low) / 2
                if middle == low or middle == high:
                    break
                sampled = _rounded_structure(middle, left, right)
                reached = sampled >= value if step > 0 else sampled <= value
                if reached:
                    high = middle
                else:
                    low = middle
            actual = _rounded_structure(high, left, right)
            if high == events[-1]["time_ms"]:
                events[-1]["value"] = actual
            elif actual != events[-1]["value"]:
                events.append({"time_ms": high, "value": actual})
    return events


def compile_legacy(source, baseline_camera):
    """Return detached tracks/conflicts; correspondence belongs to the importer."""
    if set(source) != {"molsysmovie_version", "keyframes"} or not isinstance(source["keyframes"], list):
        raise ValueError("A legacy Movie requires only its version and a keyframes list.")
    keyframes = []
    for key in source["keyframes"]:
        if (
            not isinstance(key, dict)
            or "time_ms" not in key
            or set(key) - {"time_ms", "camera", "structure_index", "layer_visibility", "easing"}
        ):
            raise ValueError("Invalid legacy Movie keyframe fields.")
        key = deepcopy(key)
        key["time_ms"] = _time(key["time_ms"], "Legacy key time")
        if keyframes and key["time_ms"] <= keyframes[-1]["time_ms"]:
            raise ValueError("Legacy Movie times must be strictly increasing.")
        easing = key.setdefault("easing", "linear")
        if not isinstance(easing, str) or easing not in _EASING:
            raise ValueError("Invalid legacy Movie easing.")
        if key.get("camera") is not None:
            key["camera"] = _camera(key["camera"])[0]
        if "structure_index" in key:
            index = key["structure_index"]
            if type(index) is not int or not 0 <= index <= _MAX_SAFE_INTEGER:
                raise ValueError("Legacy structure indices must be nonnegative safe integers.")
        if "layer_visibility" in key:
            values = key["layer_visibility"]
            if not isinstance(values, dict) or any(type(value) is not bool for value in values.values()):
                raise ValueError("Legacy visibility requires a tagged boolean mapping.")
            for tag in values:
                _tag(tag)
        keyframes.append(key)
    conflicts, tracks = [], []
    result = {
        "conflicts": conflicts,
        "tracks": tracks,
        "camera": None,
        "duration_ms": None,
        "structure_events": 0,
        "initial_structure": None,
    }
    if len(keyframes) < 2 or keyframes[-1]["time_ms"] <= 0:
        conflicts.append({"reason": "legacy_requires_multiple_keyframes"})
        return result
    result["duration_ms"] = keyframes[-1]["time_ms"]
    cameras = [key.get("camera") is not None for key in keyframes]
    if any(cameras):
        if not all(cameras):
            conflicts.append({"reason": "legacy_partial_camera_channel"})
        else:
            result["camera"] = deepcopy(keyframes[0]["camera"])
            if baseline_camera is not None and baseline_camera != result["camera"]:
                conflicts.append({"reason": "legacy_camera_override_changes_path"})
            tracks.append(
                {
                    "tag": "legacy-camera",
                    "target": {"domain": "camera"},
                    "property": "pose",
                    "keys": [
                        {"time_ms": key["time_ms"], "value": key["camera"], "easing": key["easing"]}
                        for key in keyframes
                    ],
                }
            )
    elif baseline_camera is None:
        conflicts.append({"reason": "legacy_baseline_camera_required"})
    else:
        result["camera"] = deepcopy(baseline_camera)
    structures = ["structure_index" in key for key in keyframes]
    if any(structures):
        if not all(structures):
            conflicts.append({"reason": "legacy_partial_structure_channel"})
        else:
            events = structure_events(keyframes)
            if events is None:
                conflicts.append({"reason": "legacy_structure_event_limit", "maximum": _MAX_STRUCTURE_EVENTS})
            else:
                result["structure_events"] = len(events)
                result["initial_structure"] = keyframes[0]["structure_index"]
                tracks.append(
                    {"tag": "legacy-structures", "target": {"domain": "structure"}, "property": "index", "keys": events}
                )
    visibility = {}
    for key in keyframes:
        for tag, value in key.get("layer_visibility", {}).items():
            visibility.setdefault(tag, []).append({"time_ms": key["time_ms"], "value": value})
    for index, (tag, keys) in enumerate(sorted(visibility.items())):
        if tag == "__proto__":
            # The original JS Object.assign({}, visibility) ignores a boolean
            # __proto__ entry. A typed target would introduce a new effect.
            conflicts.append({"reason": "legacy_unsupported_visibility_tag", "tag": tag})
        tracks.append(
            {
                "tag": f"legacy-visible-{index}",
                "target": {"domain": "legacy", "tag": tag},
                "property": "visible",
                "keys": keys,
            }
        )
    return result
