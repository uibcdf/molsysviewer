"""Detached Movie recipes and their headless, arbitrary-time evaluator."""

from __future__ import annotations

import bisect
import json
import math
from collections.abc import Mapping
from copy import copy, deepcopy
from numbers import Real

import numpy as np

from ._movie_appearance import (
    _CONTINUOUS,
    COLOR_INTERPOLATION,
    appearance_baseline,
    appearance_value,
    check_appearance_binding,
    interpolate_appearance,
)

MOVIE_TIMELINE_VERSION = 2
_MAX_SAFE_INTEGER = 2**53 - 1
_HALF_TURN_TOLERANCE = 1e-12
_CARTESIAN_CAMERA = "cartesian-constant-up@1"
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


def _cartesian_segments(baseline, tracks):
    """Reject an unsafe straight segment before admitting a Cartesian plan."""
    keys = next((track["keys"] for track in tracks if track["property"] == "pose"), [])
    previous = baseline
    for key in keys:
        current = key["value"]
        if key["time_ms"] == 0:
            previous = current
            continue
        if previous["up"] != current["up"]:
            raise ValueError("Cartesian Movie camera segments require a constant up vector.")
        up_length = math.hypot(*previous["up"])
        up = [value / up_length for value in previous["up"]]
        directions = []
        for pose in (previous, current):
            directions.append([a - b for a, b in zip(pose["position"], pose["target"], strict=True)])
        for field in ("position", "target"):
            if any(not math.isfinite(b - a) for a, b in zip(previous[field], current[field], strict=True)):
                raise ValueError("Cartesian Movie camera segment exceeds the finite coordinate range.")
        scale = max(math.hypot(*value) for value in directions)
        perpendicular = []
        for direction in directions:
            x, y, z = (value / scale for value in direction)
            perpendicular.append([up[1] * z - up[2] * y, up[2] * x - up[0] * z, up[0] * y - up[1] * x])
        start, end = perpendicular
        delta = [b - a for a, b in zip(start, end, strict=True)]
        denominator = sum(value * value for value in delta)
        fraction = (
            min(1.0, max(0.0, -sum(a * b for a, b in zip(start, delta, strict=True)) / denominator))
            if denominator
            else 0.0
        )
        closest = math.hypot(*(a + fraction * b for a, b in zip(start, delta, strict=True)))
        # |direction(t)| is at most the endpoint scale. This conservative
        # bound protects every point, including unsampled focus crossings.
        if closest <= 1e-12:
            raise ValueError("Cartesian Movie camera segment crosses an unsafe viewing direction.")
        previous = current


def _interpolate_cartesian_camera(left, right, fraction):
    return {
        field: [a + (b - a) * fraction for a, b in zip(left[field], right[field], strict=True)]
        for field in ("position", "target", "up")
    }


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
    if channel != "visible":
        return appearance_value(value, channel)
    if type(value) is not bool:
        raise ValueError("Movie visibility keys require boolean values.")
    return value


def _track(track, visibility, count, duration, scene):
    track = _record(track, ("tag", "target", "property", "keys"), "Movie track")
    tag = _tag(track["tag"])
    target = track["target"]
    if not isinstance(target, Mapping) or set(target) - {"domain", "tag"} or not isinstance(target.get("domain"), str):
        raise ValueError("Movie target requires a domain and, for a scene object, its tag.")
    domain = target["domain"]
    target_tag = target.get("tag")
    prop = track["property"]
    expected = {"camera": "pose", "structure": "index"}.get(domain, "visible")
    if (
        not isinstance(prop, str)
        or prop != expected
        and (domain in {"camera", "structure"} or prop in {"pose", "index"})
    ):
        raise ValueError(f"Movie property {prop!r} is unsupported for {domain!r}.")
    if domain in {"camera", "structure", "whole", "scene"}:
        if target_tag is not None:
            raise ValueError(f"Movie target {domain!r} has no tag.")
    else:
        target_tag = _tag(target_tag)
    if prop == "visible" and (domain, target_tag) not in visibility:
        raise ValueError(f"Unknown Movie visibility target {(domain, target_tag)!r}.")
    initial = appearance_baseline(scene, domain, target_tag, prop) if prop not in {"pose", "index", "visible"} else None
    if domain == "scene" and initial is None:
        raise ValueError(
            "Configure an explicit RGB background or both lighting intensities before capturing the Movie baseline."
        )
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
        if (
            not isinstance(easing, str)
            or easing not in _EASING
            or (prop not in {"pose", *_CONTINUOUS} and easing != "linear")
        ):
            raise ValueError("Only continuous Movie properties admit a non-linear easing.")
        keys.append({"time_ms": time, "value": _value(key["value"], prop, count), "easing": easing})
    if prop not in {"pose", "index", "visible"} and initial is None and keys[0]["time_ms"] != 0:
        raise ValueError("This Movie appearance has no explicit baseline value; provide a key at time zero.")
    return {
        "tag": tag,
        "target": {"domain": domain, **({"tag": target_tag} if target_tag is not None else {})},
        "property": prop,
        "keys": keys,
    }


def _channel(track):
    target = track["target"]
    return target["domain"], target.get("tag"), track["property"]


def _tracks(records, visibility, count, duration, scene):
    if not isinstance(records, (list, tuple)):
        raise ValueError("Movie tracks must be an ordered list.")
    tracks = [_track(track, visibility, count, duration, scene) for track in records]
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


def _binding(value):
    binding = _record(value, ("n_atoms", "n_structures", "fingerprint"), "Movie molecular binding")
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
    return dict(binding)


def _tracked_visibility(tracks, visibility):
    targets = {(domain, tag) for domain, tag, prop in map(_channel, tracks) if prop == "visible"}
    return {key: row for key, row in visibility.items() if key in targets}


class _MovieTimeline:
    """Store validated, detached data and replace it only after a complete check."""

    def __init__(self, data):
        fields = ("molsysmovie_version", "duration_ms", "units", "baseline", "tracks")
        if isinstance(data, Mapping) and "color_interpolation" in data:
            fields += ("color_interpolation",)
        if isinstance(data, Mapping) and "camera_interpolation" in data:
            fields += ("camera_interpolation",)
        if isinstance(data, Mapping) and "provenance" in data:
            fields += ("provenance",)
        data = _record(data, fields, "Movie recipe")
        if "color_interpolation" in data and data["color_interpolation"] != COLOR_INTERPOLATION:
            raise ValueError("Unsupported Movie colour interpolation contract.")
        if "camera_interpolation" in data and data["camera_interpolation"] != _CARTESIAN_CAMERA:
            raise ValueError("Unsupported Movie camera interpolation contract.")
        if type(data["molsysmovie_version"]) is not int or data["molsysmovie_version"] != MOVIE_TIMELINE_VERSION:
            raise ValueError("Unsupported Movie recipe version.")
        if data["units"] != {"time": "ms", "camera_length": "angstrom"}:
            raise ValueError("Movie recipes use milliseconds and angstroms.")
        duration = _duration(data["duration_ms"])
        baseline_fields = ("scene", "camera", "binding")
        if isinstance(data["baseline"], Mapping) and "environment_capture" in data["baseline"]:
            baseline_fields += ("environment_capture",)
        baseline = _record(data["baseline"], baseline_fields, "Movie baseline")
        binding = _binding(baseline["binding"])
        scene = baseline["scene"]
        if not isinstance(scene, Mapping) or scene.get("version") != 2 or "movie" in scene:
            raise ValueError("Movie baseline requires a version-2 overlay scene without a nested Movie.")
        scene = json.loads(json.dumps(dict(scene), allow_nan=False))
        if "environment" in scene:
            from .._scene_environment import validate_environment

            scene["environment"] = validate_environment(scene["environment"])
        capture = None
        if "environment_capture" in baseline:
            from ._movie_environment import environment_capture

            capture = environment_capture(baseline["environment_capture"], scene.get("environment"))
        sources = scene.get("sources")
        if sources is not None and (not isinstance(sources, dict) or sources.get("binding") != binding):
            raise ValueError("Movie baseline source records do not match its molecular binding.")
        view_state = scene.get("view")
        if not isinstance(view_state, dict) or "structure_index" not in view_state:
            raise ValueError("Movie baseline requires its visible structure index.")
        index = _index(view_state["structure_index"], binding["n_structures"])
        visibility = _scene_visibility(scene)
        camera = _camera(baseline["camera"])[0]
        tracks = _tracks(data["tracks"], visibility, binding["n_structures"], duration, scene)
        if "camera_interpolation" in data:
            _cartesian_segments(camera, tracks)
        has_color = any(track["property"] in {"color", "background"} for track in tracks)
        if has_color and data.get("color_interpolation") != COLOR_INTERPOLATION:
            raise ValueError("Movie colour tracks require their explicit interpolation contract.")
        self._data = {
            "molsysmovie_version": MOVIE_TIMELINE_VERSION,
            "duration_ms": duration,
            "units": {"time": "ms", "camera_length": "angstrom"},
            "baseline": {
                "scene": scene,
                "camera": camera,
                "binding": dict(binding),
                **({"environment_capture": capture} if capture is not None else {}),
            },
            "tracks": tracks,
            **({"color_interpolation": COLOR_INTERPOLATION} if has_color else {}),
            **({"camera_interpolation": _CARTESIAN_CAMERA} if "camera_interpolation" in data else {}),
        }
        if "provenance" in data:
            from ._movie_import import validate_provenance

            self._data["provenance"] = validate_provenance(
                data["provenance"], destination_count=binding["n_structures"]
            )
        self._index = index
        self._visibility = visibility
        self._tracked_visibility = _tracked_visibility(self._data["tracks"], visibility)

    def to_dict(self):
        return deepcopy(self._data)

    def preview_recipe(self):
        """Send the clock only the baseline fields it needs to evaluate tracks."""
        scene = {
            "version": 2,
            "view": {"structure_index": self._index},
            "whole": {"visible": self._visibility["whole", None][0]},
        }
        for (domain, tag), (visible, _) in self._tracked_visibility.items():
            if domain != "whole":
                scene.setdefault(_VISIBILITY_DOMAINS[domain], []).append({"tag": tag, "hidden": not visible})
        original = self._data["baseline"]["scene"]
        if "environment" in original:
            scene["environment"] = original["environment"]
        for track in self._data["tracks"]:
            domain, tag, prop = _channel(track)
            if prop in {"pose", "index", "visible"} or domain == "scene":
                continue
            if domain == "whole":
                scene["whole"].update(
                    {key: original["whole"].get(key) for key in ("representation", "preset", "params")}
                )
                continue
            records = scene.setdefault(_VISIBILITY_DOMAINS[domain], [])
            current = next((row for row in records if row["tag"] == tag), None)
            if current is None:
                current = {"tag": tag, "hidden": not self._visibility[domain, tag][0]}
                records.append(current)
            source = next(row for row in original[_VISIBILITY_DOMAINS[domain]] if row["tag"] == tag)
            if domain == "region":
                current.update({key: source.get(key) for key in ("representation", "preset", "params")})
            elif domain == "interaction":
                current["style"] = source["style"]
            else:
                current.update(
                    op=source["op"],
                    options={
                        key: value for key, value in source["options"].items() if key in {"color", "alpha", "text"}
                    },
                )
        baseline = {**self._data["baseline"], "scene": scene}
        preview = {**self._data, "baseline": baseline}
        preview.pop("provenance", None)  # The renderer needs no source/import history.
        return deepcopy(preview)

    def edit(self, *, duration, tracks):
        """Keep the privately owned baseline and replace validated tracks as a unit."""
        duration = _duration(duration)
        tracks = _tracks(
            tracks,
            self._visibility,
            self._data["baseline"]["binding"]["n_structures"],
            duration,
            self._data["baseline"]["scene"],
        )
        if "camera_interpolation" in self._data:
            _cartesian_segments(self._data["baseline"]["camera"], tracks)
        revised = copy(self)
        revised._data = {**self._data, "duration_ms": duration, "tracks": tracks}
        if any(track["property"] in {"color", "background"} for track in tracks):
            revised._data["color_interpolation"] = COLOR_INTERPOLATION
        else:
            revised._data.pop("color_interpolation", None)
        revised._tracked_visibility = _tracked_visibility(tracks, self._visibility)
        return revised

    def track_records(self):
        return deepcopy(self._data["tracks"])

    def rebased(self, scene, camera, binding, *, environment_capture=None):
        data = self.to_dict()
        data["baseline"] = {"scene": scene, "camera": camera, "binding": binding}
        if environment_capture is not None:
            data["baseline"]["environment_capture"] = environment_capture
        revised = _MovieTimeline(data)
        # Existing keys are already validated; preserve their exact serialized
        # values rather than normalizing camera vectors a second time.
        revised._data["tracks"] = self.track_records()
        return revised

    def check_scene(self, scene):
        from ._movie_scene import check_scene

        check_scene(self, scene, _VISIBILITY_DOMAINS)

    @property
    def duration_ms(self):
        return self._data["duration_ms"]

    @property
    def n_tracks(self):
        return len(self._data["tracks"])

    def visibility_targets(self):
        return tuple(self._tracked_visibility)

    @property
    def has_appearance(self):
        return any(track["property"] not in {"pose", "index", "visible"} for track in self._data["tracks"])

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
            if prop == "visible" or prop not in {"pose", "index"} and domain != "scene":
                key = (domain, tag)
                if key not in current or current[key][1] != self._visibility[key][1]:
                    raise ValueError(f"Movie scene target {key!r} is missing or changed.")
                if prop != "visible":
                    appearance_baseline(scene, domain, tag, prop)
        check_appearance_binding(self._data["baseline"]["scene"], scene, self._data["tracks"])

    def evaluate(self, time_ms, *, tracked_visibility=False):
        time = _time(time_ms, "Movie time", self.duration_ms)
        camera = self._data["baseline"]["camera"]
        index = self._index
        targets = self._tracked_visibility if tracked_visibility else self._visibility
        visibility = {key: row[0] for key, row in targets.items()}
        appearance = []
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
                    interpolate = (
                        _interpolate_cartesian_camera if "camera_interpolation" in self._data else _interpolate_camera
                    )
                    camera = interpolate(left["value"], end["value"], _ease(fraction, left["easing"]))
            elif prop not in {"index", "visible"}:
                initial = appearance_baseline(self._data["baseline"]["scene"], domain, tag, prop)
                left = keys[right - 1] if right else {"time_ms": 0, "value": initial, "easing": "linear"}
                value = left["value"]
                if prop in _CONTINUOUS and right < len(keys) and left["time_ms"] != time:
                    end = keys[right]
                    fraction = _ease((time - left["time_ms"]) / (end["time_ms"] - left["time_ms"]), left["easing"])
                    value = interpolate_appearance(value, end["value"], fraction, prop)
                appearance.append({"domain": domain, "tag": tag, "property": prop, "value": deepcopy(value)})
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
            **({"appearance": appearance} if appearance else {}),
            "visibility": [
                {"domain": domain, "tag": tag, "visible": value} for (domain, tag), value in visibility.items()
            ],
        }
