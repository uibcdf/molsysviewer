"""Detached Movie recipes and their headless, arbitrary-time evaluator."""

from __future__ import annotations

import bisect
import json
import math
from collections.abc import Mapping
from copy import copy, deepcopy
from numbers import Real

import numpy as np

MOVIE_TIMELINE_VERSION = 2
_MAX_SAFE_INTEGER = 2**53 - 1
_HALF_TURN_TOLERANCE = 1e-12
_EASING = {"linear", "ease-in", "ease-out", "ease-in-out"}
_VISIBILITY_DOMAINS = {
    "annotation": "annotations",
    "interaction": "interactions",
    "layer": "layers",
    "measurement": "measurements",
    "region": "regions",
    "shape": "shapes",
}


def _record(value, fields, label):
    if not isinstance(value, Mapping) or set(value) != set(fields):
        raise ValueError(f"{label} must contain {', '.join(fields)}.")
    return value


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number.")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"{label} must be a finite number.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number.")
    return result


def _time(value, label, maximum=_MAX_SAFE_INTEGER):
    result = _number(value, label)
    if not 0 <= result <= maximum:
        raise ValueError(f"{label} must be between 0 and {maximum} ms.")
    return result


def _index(value, count):
    if type(value) is not int or not 0 <= value < count:
        raise ValueError(f"Structure index must be an integer in [0, {count}).")
    return value


def _tag(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("A Movie track or scene target requires a nonempty tag.")
    return value


def _vector(value, label):
    if isinstance(value, np.ndarray) and value.shape != (3,):
        raise ValueError(f"Camera {label} must have three finite components.")
    if not isinstance(value, (list, tuple, np.ndarray)) or len(value) != 3:
        raise ValueError(f"Camera {label} must have three finite components.")
    return np.array([_number(v, f"Camera {label}") for v in value], dtype=float)


def _camera(value):
    if not isinstance(value, Mapping) or not {"position", "target", "up"} <= set(value):
        raise ValueError("Camera pose requires position, target and up.")
    position = _vector(value["position"], "position")
    target = _vector(value["target"], "target")
    up = _vector(value["up"], "up")
    pose = {"position": position.tolist(), "target": target.tolist(), "up": up.tolist()}
    with np.errstate(over="ignore", invalid="ignore"):
        backward = position - target
        distance = math.hypot(*backward)
    up_norm = math.hypot(*up)
    if not math.isfinite(distance) or distance <= 0 or not math.isfinite(up_norm) or up_norm <= 0:
        raise ValueError("Camera pose requires a positive finite distance and a nonzero up vector.")
    backward /= distance
    right = np.cross(up / up_norm, backward)
    norm = math.hypot(*right)
    if norm < 1e-12:
        raise ValueError("Camera up must not be parallel to its viewing direction.")
    right /= norm
    up = np.cross(backward, right)
    # Preserve the submitted pose. Its orthonormal basis is derived for interpolation.
    return pose, (target, distance, np.column_stack((right, up, backward)))


def _quaternion(matrix):
    """Convert an orthonormal rotation matrix to an XYZW unit quaternion."""
    trace = float(np.trace(matrix))
    if trace > 0:
        scale = 2 * math.sqrt(1 + trace)
        return np.array(
            [
                (matrix[2, 1] - matrix[1, 2]) / scale,
                (matrix[0, 2] - matrix[2, 0]) / scale,
                (matrix[1, 0] - matrix[0, 1]) / scale,
                scale / 4,
            ]
        )
    i = int(np.argmax(np.diag(matrix)))
    j, k = (i + 1) % 3, (i + 2) % 3
    scale = 2 * math.sqrt(1 + matrix[i, i] - matrix[j, j] - matrix[k, k])
    result = np.empty(4)
    result[i] = scale / 4
    result[j] = (matrix[j, i] + matrix[i, j]) / scale
    result[k] = (matrix[k, i] + matrix[i, k]) / scale
    result[3] = (matrix[k, j] - matrix[j, k]) / scale
    return result


def _rotate(quaternion, axis):
    vector, scalar = quaternion[:3], quaternion[3]
    twice_cross = 2 * np.cross(vector, axis)
    return axis + scalar * twice_cross + np.cross(vector, twice_cross)


def _canonical_quaternion(quaternion):
    first = next(component for component in quaternion if abs(component) > _HALF_TURN_TOLERANCE)
    return -quaternion if first < 0 else quaternion


def _interpolate_camera(left, right, fraction):
    _, (target_a, distance_a, basis_a) = _camera(left)
    _, (target_b, distance_b, basis_b) = _camera(right)
    a, b = _quaternion(basis_a), _quaternion(basis_b)
    dot = float(a @ b)
    if abs(dot) <= _HALF_TURN_TOLERANCE:
        # Both arcs have the same length at a half turn. A fixed quaternion
        # sign and zero cosine prevent roundoff from choosing opposite arcs.
        a, b = _canonical_quaternion(a), _canonical_quaternion(b)
        dot = 0.0
    if dot < 0:
        b, dot = -b, -dot
    if dot > 0.9995:
        orientation = (1 - fraction) * a + fraction * b
    else:
        angle = math.acos(dot)
        orientation = (math.sin((1 - fraction) * angle) * a + math.sin(fraction * angle) * b) / math.sin(angle)
    orientation /= math.hypot(*orientation)
    target = (1 - fraction) * target_a + fraction * target_b
    distance = (1 - fraction) * distance_a + fraction * distance_b
    with np.errstate(over="ignore", invalid="ignore"):
        position = target + distance * _rotate(orientation, (0, 0, 1))
    if not np.all(np.isfinite(position)):
        raise ValueError("Interpolated camera position exceeds the finite coordinate range.")
    return {"position": position.tolist(), "target": target.tolist(), "up": _rotate(orientation, (0, 1, 0)).tolist()}


def _ease(fraction, easing):
    if easing == "ease-in":
        return fraction**2
    if easing == "ease-out":
        return 1 - (1 - fraction) ** 2
    if easing == "ease-in-out":
        return 2 * fraction**2 if fraction < 0.5 else 1 - 2 * (1 - fraction) ** 2
    return fraction


def _scene_visibility(scene):
    whole = scene.get("whole")
    if not isinstance(whole, dict) or type(whole.get("visible")) is not bool:
        raise ValueError("Movie baseline requires the whole-system visibility.")
    visibility = {("whole", None): (whole["visible"], None)}
    for domain, collection in _VISIBILITY_DOMAINS.items():
        records = scene.get(collection, [])
        if not isinstance(records, list):
            raise ValueError(f"Movie scene {collection} must be a list.")
        for record in records:
            if not isinstance(record, dict) or type(record.get("hidden", False)) is not bool:
                raise ValueError(f"Invalid {domain} visibility in Movie baseline.")
            key = (domain, _tag(record.get("tag")))
            if key in visibility:
                raise ValueError(f"Ambiguous Movie target {key!r}.")
            identity = (
                record.get("uid")
                if domain == "region"
                else record.get("analysis_revision")
                if domain == "interaction"
                else None
            )
            visibility[key] = (not record.get("hidden", False), identity)
    return visibility


def _value(value, channel, count):
    if channel == "pose":
        return _camera(value)[0]
    if channel == "index":
        return _index(value, count)
    if type(value) is not bool:
        raise ValueError("Movie visibility keys require boolean values.")
    return value


def _track(track, visibility, count, duration):
    track = _record(track, ("tag", "target", "property", "keys"), "Movie track")
    tag = _tag(track["tag"])
    target = track["target"]
    if not isinstance(target, Mapping) or set(target) - {"domain", "tag"} or not isinstance(target.get("domain"), str):
        raise ValueError("Movie target requires a domain and, for a scene object, its tag.")
    domain = target["domain"]
    target_tag = target.get("tag")
    prop = track["property"]
    expected = {"camera": "pose", "structure": "index"}.get(domain, "visible")
    if prop != expected:
        raise ValueError(f"Movie property {prop!r} is unsupported for {domain!r}.")
    if domain in {"camera", "structure", "whole"}:
        if target_tag is not None:
            raise ValueError(f"Movie target {domain!r} has no tag.")
    else:
        target_tag = _tag(target_tag)
    if prop == "visible" and (domain, target_tag) not in visibility:
        raise ValueError(f"Unknown Movie visibility target {(domain, target_tag)!r}.")
    if not isinstance(track["keys"], (list, tuple)) or not track["keys"]:
        raise ValueError("A Movie track requires at least one key.")
    keys = []
    for key in track["keys"]:
        if (
            not isinstance(key, Mapping)
            or not {"time_ms", "value"} <= set(key)
            or set(key) - {"time_ms", "value", "easing"}
        ):
            raise ValueError("A Movie key requires time_ms and value, with optional easing.")
        time = _time(key["time_ms"], "Key time", duration)
        if keys and time <= keys[-1]["time_ms"]:
            raise ValueError("Movie keys in one track must be strictly increasing.")
        easing = key.get("easing", "linear")
        if not isinstance(easing, str) or easing not in _EASING or (prop != "pose" and easing != "linear"):
            raise ValueError("Only camera pose keys admit a non-linear easing.")
        keys.append({"time_ms": time, "value": _value(key["value"], prop, count), "easing": easing})
    return {
        "tag": tag,
        "target": {"domain": domain, **({"tag": target_tag} if target_tag is not None else {})},
        "property": prop,
        "keys": keys,
    }


def _channel(track):
    target = track["target"]
    return target["domain"], target.get("tag"), track["property"]


def _tracks(records, visibility, count, duration):
    if not isinstance(records, (list, tuple)):
        raise ValueError("Movie tracks must be an ordered list.")
    tracks = [_track(track, visibility, count, duration) for track in records]
    if len({track["tag"] for track in tracks}) != len(tracks):
        raise ValueError("Movie track tags must be unique.")
    if len({_channel(track) for track in tracks}) != len(tracks):
        raise ValueError("Movie permits only one track per target property.")
    return tracks


def _duration(value):
    duration = _time(value, "Movie duration")
    if duration <= 0:
        raise ValueError("Movie duration must be positive.")
    return duration


class _MovieTimeline:
    """Store validated, detached data and replace it only after a complete check."""

    def __init__(self, data):
        data = _record(data, ("molsysmovie_version", "duration_ms", "units", "baseline", "tracks"), "Movie recipe")
        if type(data["molsysmovie_version"]) is not int or data["molsysmovie_version"] != MOVIE_TIMELINE_VERSION:
            raise ValueError("Unsupported Movie recipe version.")
        if data["units"] != {"time": "ms", "camera_length": "angstrom"}:
            raise ValueError("Movie recipes use milliseconds and angstroms.")
        duration = _duration(data["duration_ms"])
        baseline = _record(data["baseline"], ("scene", "camera", "binding"), "Movie baseline")
        binding = _record(baseline["binding"], ("n_atoms", "n_structures", "fingerprint"), "Movie molecular binding")
        for field in ("n_atoms", "n_structures"):
            if type(binding[field]) is not int or not 0 < binding[field] <= _MAX_SAFE_INTEGER:
                raise ValueError(f"Movie molecular binding requires a positive {field}.")
        fingerprint = binding["fingerprint"]
        if (
            not isinstance(fingerprint, str)
            or not fingerprint.startswith("sha256:")
            or len(fingerprint) != 71
            or any(c not in "0123456789abcdef" for c in fingerprint[7:])
        ):
            raise ValueError("Movie molecular binding requires a SHA-256 fingerprint.")
        scene = baseline["scene"]
        if not isinstance(scene, Mapping) or scene.get("version") != 2 or "movie" in scene:
            raise ValueError("Movie baseline requires a version-2 overlay scene without a nested Movie.")
        scene = json.loads(json.dumps(dict(scene), allow_nan=False))
        sources = scene.get("sources")
        if sources is not None and (not isinstance(sources, dict) or sources.get("binding") != binding):
            raise ValueError("Movie baseline source records do not match its molecular binding.")
        view_state = scene.get("view")
        if not isinstance(view_state, dict) or "structure_index" not in view_state:
            raise ValueError("Movie baseline requires its visible structure index.")
        index = _index(view_state["structure_index"], binding["n_structures"])
        visibility = _scene_visibility(scene)
        camera = _camera(baseline["camera"])[0]
        self._data = {
            "molsysmovie_version": MOVIE_TIMELINE_VERSION,
            "duration_ms": duration,
            "units": {"time": "ms", "camera_length": "angstrom"},
            "baseline": {"scene": scene, "camera": camera, "binding": dict(binding)},
            "tracks": _tracks(data["tracks"], visibility, binding["n_structures"], duration),
        }
        self._index = index
        self._visibility = visibility

    def to_dict(self):
        return deepcopy(self._data)

    def edit(self, *, duration, tracks):
        """Keep the privately owned baseline and replace validated tracks as a unit."""
        duration = _duration(duration)
        tracks = _tracks(tracks, self._visibility, self._data["baseline"]["binding"]["n_structures"], duration)
        revised = copy(self)
        revised._data = {**self._data, "duration_ms": duration, "tracks": tracks}
        return revised

    def track_records(self):
        return deepcopy(self._data["tracks"])

    @property
    def duration_ms(self):
        return self._data["duration_ms"]

    @property
    def n_tracks(self):
        return len(self._data["tracks"])

    def check_binding(self, binding, scene=None):
        if self._data["baseline"]["binding"] != binding:
            raise ValueError(
                "Movie molecular binding differs from the loaded system. Capture a new baseline or import the matching system."
            )
        if scene is None:
            return
        if self._data["baseline"]["scene"].get("structure") != scene.get("structure"):
            raise ValueError("Movie baseline scene describes a different ordered structure.")
        current = _scene_visibility(scene)
        for track in self._data["tracks"]:
            domain, tag, prop = _channel(track)
            if prop == "visible":
                key = (domain, tag)
                if key not in current or current[key][1] != self._visibility[key][1]:
                    raise ValueError(f"Movie scene target {key!r} is missing or changed.")

    def evaluate(self, time_ms):
        time = _time(time_ms, "Movie time", self.duration_ms)
        camera = self._data["baseline"]["camera"]
        index = self._index
        visibility = {key: row[0] for key, row in self._visibility.items()}
        for track in self._data["tracks"]:
            domain, tag, prop = _channel(track)
            keys = track["keys"]
            right = bisect.bisect_right(keys, time, key=lambda item: item["time_ms"])
            if prop == "pose":
                left = keys[right - 1] if right else {"time_ms": 0, "value": camera, "easing": "linear"}
                if right == len(keys) or left["time_ms"] == time:
                    camera = left["value"]
                else:
                    end = keys[right]
                    fraction = (time - left["time_ms"]) / (end["time_ms"] - left["time_ms"])
                    camera = _interpolate_camera(left["value"], end["value"], _ease(fraction, left["easing"]))
            elif right:
                value = keys[right - 1]["value"]
                if prop == "index":
                    index = value
                else:
                    visibility[(domain, tag)] = value
        pose, (_, _, basis) = _camera(camera)
        pose["up"] = basis[:, 1].tolist()
        return {
            "time_ms": time,
            "camera": pose,
            "structure_index": index,
            "visibility": [
                {"domain": domain, "tag": tag, "visible": value} for (domain, tag), value in visibility.items()
            ],
        }
