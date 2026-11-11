"""Movie's bounded appearance catalogue, colour interpolation and scene adapters."""

import math
from contextlib import nullcontext
from copy import deepcopy
from numbers import Real

from .representations import ALLOWED_REPRESENTATIONS

_PROPERTIES = {
    "whole": {"representation", "color", "alpha"},
    "region": {"representation", "color", "alpha"},
    "shape": {"color", "alpha"},
    "interaction": {"color", "alpha"},
    "annotation": {"text"},
    "scene": {"background", "lighting"},
}
_CONTINUOUS = {"color", "alpha", "background", "lighting"}
COLOR_INTERPOLATION = "linear-light-srgb-half-up@1"


def appearance_value(value, prop):
    if prop in {"color", "background"}:
        if type(value) is not int or not 0 <= value <= 0xFFFFFF:
            raise ValueError("Movie colours must be 24-bit RGB integers.")
        return value
    if prop == "alpha":
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("Movie alpha must be a finite number in [0, 1].")
        return float(value)
    if prop == "lighting":
        if not isinstance(value, dict) or set(value) != {"ambient", "diffuse"}:
            raise ValueError("Movie lighting requires explicit ambient and diffuse intensities.")
        return {key: appearance_value(value[key], "alpha") for key in ("ambient", "diffuse")}
    if prop == "representation":
        if not isinstance(value, str) or value not in ALLOWED_REPRESENTATIONS:
            raise ValueError("Movie representation must be a canonical public molecular representation type.")
        return value
    if prop == "text" and isinstance(value, str):
        return value
    raise ValueError(f"Unsupported Movie appearance value for {prop!r}.")


def appearance_baseline(scene, domain, tag, prop):
    if prop not in _PROPERTIES.get(domain, ()):
        raise ValueError(f"Movie property {prop!r} is unsupported for {domain!r}.")
    if domain == "scene":
        environment = scene.get("environment", {})
        value = environment.get("lighting") if prop == "lighting" else environment.get("background", {}).get("color")
        if prop == "lighting" and (not isinstance(value, dict) or set(value) != {"ambient", "diffuse"}):
            return None
        return None if value is None else appearance_value(value, prop)
    collection = {"region": "regions", "shape": "shapes", "interaction": "interactions", "annotation": "annotations"}
    record = (
        scene.get("whole")
        if domain == "whole"
        else next((row for row in scene.get(collection[domain], []) if row.get("tag") == tag), None)
    )
    if record is None:
        raise ValueError(f"Unknown Movie appearance target {(domain, tag)!r}.")
    if domain in {"whole", "region"}:
        if record.get("preset") is not None or record.get("representation") not in ALLOWED_REPRESENTATIONS:
            raise ValueError("Movie structural appearance requires an explicit simple baseline representation.")
        params = record.get("params", {})
        if not isinstance(params, dict):
            raise ValueError("Movie structural parameters must be a dictionary.")
        if prop == "color" and record.get("color_layer"):
            raise ValueError("Movie uniform colour requires no per-atom colour layer on its target.")
        if prop == "representation":
            value = record["representation"]
        elif prop == "alpha":
            value = params.get("alpha", 1)
        else:
            theme = params.get("molstar_color_theme", {})
            value = (
                theme.get("params", {}).get("value")
                if isinstance(theme, dict) and theme.get("name") == "uniform"
                else None
            )
    elif domain == "shape":
        if record.get("op") != "add_sphere":
            raise ValueError("Movie shape colour/alpha currently requires a sphere.")
        value = record.get("options", {}).get(prop)
    elif domain == "interaction":
        value = record.get("style", {}).get(prop)
    else:
        value = record.get("options", {}).get("text")
    return None if value is None else appearance_value(value, prop)


def check_appearance_binding(baseline, current, tracks):
    """A property track may change its fields, but not silently redefine others."""
    grouped = {}
    for track in tracks:
        if track["property"] in {"pose", "index", "visible"}:
            continue
        target = track["target"]
        grouped.setdefault((target["domain"], target.get("tag")), set()).add(track["property"])
    for (domain, tag), properties in grouped.items():
        if domain not in {"whole", "region"}:
            continue

        def identity(scene, domain=domain, tag=tag, properties=properties):
            record = scene["whole"] if domain == "whole" else next(row for row in scene["regions"] if row["tag"] == tag)
            params = deepcopy(record.get("params", {}))
            if "alpha" in properties:
                params.pop("alpha", None)
            if "color" in properties:
                params.pop("molstar_color_theme", None)
                params.pop("color_scheme", None)
            return (
                None if "representation" in properties else record.get("representation"),
                record.get("preset"),
                params,
            )

        if identity(baseline) != identity(current):
            raise ValueError("Movie target has changed untracked material settings; capture a reviewed new baseline.")


def interpolate_appearance(left, right, fraction, prop):
    if prop in {"color", "background"}:

        def linear(channel):
            value = channel / 255
            return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

        result = 0
        for shift in (16, 8, 0):
            a, b = linear((left >> shift) & 255), linear((right >> shift) & 255)
            value = (1 - fraction) * a + fraction * b
            encoded = 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055
            result |= min(255, max(0, math.floor(encoded * 255 + 0.5))) << shift
        return result
    if prop == "lighting":
        return {key: (1 - fraction) * left[key] + fraction * right[key] for key in ("ambient", "diffuse")}
    return (1 - fraction) * left + fraction * right


def appearance_commands(view, timeline, sample):
    """Preflight every target, then return existing-owner calls for differences."""
    rows = sample.get("appearance", [])
    baseline = timeline._data["baseline"]
    if "environment_capture" in baseline:
        # Replay observed constants too; tracked channels supply their final
        # value directly, without a baseline-then-key flash.
        owned = {row["property"] for row in rows if row["domain"] == "scene"}
        rows = [*rows]
        for prop, value in baseline["scene"]["environment"].items():
            if prop not in owned:
                rows.append(
                    {
                        "domain": "scene",
                        "tag": None,
                        "property": prop,
                        "value": value["color"] if prop == "background" else value,
                    }
                )
    targets = {}
    for row in rows:
        domain, tag = row["domain"], row["tag"]
        if domain not in {"whole", "scene"}:
            target = getattr(
                view,
                {"region": "regions", "shape": "shapes", "interaction": "interactions", "annotation": "annotations"}[
                    domain
                ],
            ).get(tag)
            if target is None:
                raise ValueError(f"Movie scene target {(domain, tag)!r} is missing.")
            targets[domain, tag] = target
    commands = []
    groups = {}
    for row in rows:
        domain, tag, prop, value = row["domain"], row["tag"], row["property"], row["value"]
        if domain in {"whole", "region"}:
            groups.setdefault((domain, tag), {})[prop] = value
            continue
        if domain == "scene":
            from .._scene_environment import export_environment

            current = export_environment(view)
            if prop == "background":
                if current.get("background") != {"color": value}:
                    commands.append(lambda value=value: view.scene.set_background(value, skip_digestion=True))
            elif current.get("lighting") != value:
                commands.append(lambda value=value: view.scene.set_lighting(**value, skip_digestion=True))
            continue
        target = targets[domain, tag]
        if domain == "shape":
            current = target._require_shape_message()["options"].get(prop)
        elif domain == "interaction":
            current = target._style.get(prop)
        else:
            current = next(row for row in view.annotations.records() if row["tag"] == tag)["options"].get(prop)
        if current != value:
            setter = getattr(target, {"text": "set_text", "color": "set_color", "alpha": "set_alpha"}[prop])
            commands.append(lambda setter=setter, value=value: setter(value, skip_digestion=True))
    for (domain, tag), values in groups.items():
        target = view.whole if domain == "whole" else targets[domain, tag]
        baseline = timeline._data["baseline"]["scene"]
        record = (
            baseline["whole"] if domain == "whole" else next(row for row in baseline["regions"] if row["tag"] == tag)
        )
        params = deepcopy(record.get("params", {}))
        representation = values.get("representation", record["representation"])
        if "color" in values:
            params.pop("color_scheme", None)
            params["molstar_color_theme"] = {"name": "uniform", "params": {"value": values["color"]}}
        if "alpha" in values:
            params["alpha"] = values["alpha"]
        current = target.params if domain == "whole" else target.repr_params
        if target.representation == representation and target.preset is None and current == params:
            continue

        def apply(target=target, domain=domain, representation=representation, params=params):
            # Retain priority throughout the setter and transport; do not
            # temporarily raise a region and issue a second correction.
            with view._retain_region_order(target) if domain == "region" else nullcontext():
                target.set_representation(representation, skip_digestion=True, **params)

        commands.append(apply)
    return commands
