"""Validated, replayable environment intent shared by state and Movie."""

import math
from copy import deepcopy
from numbers import Real


def validate_environment(value):
    if not isinstance(value, dict) or set(value) - {"background", "lighting"}:
        raise ValueError("Scene environment supports background and lighting only.")
    result = {}
    if "background" in value:
        background = value["background"]
        if not isinstance(background, dict) or len(background) != 1:
            raise ValueError("Scene background requires one colour or mode.")
        if set(background) == {"color"}:
            color = background["color"]
            if type(color) is not int or not 0 <= color <= 0xFFFFFF:
                raise ValueError("Scene background colour must be a 24-bit RGB integer.")
        elif set(background) != {"mode"} or background["mode"] not in ("light", "dark"):
            raise ValueError("Scene background mode must be light or dark.")
        result["background"] = dict(background)
    if "lighting" in value:
        lighting = value["lighting"]
        if not isinstance(lighting, dict) or not lighting or set(lighting) - {"ambient", "diffuse"}:
            raise ValueError("Scene lighting supports ambient and diffuse intensity.")
        result["lighting"] = {}
        for key, number in lighting.items():
            if (
                isinstance(number, bool)
                or not isinstance(number, Real)
                or not math.isfinite(number)
                or not 0 <= number <= 1
            ):
                raise ValueError("Scene lighting intensities must be finite numbers in [0, 1].")
            result["lighting"][key] = float(number)
    return result


def export_environment(view):
    look = view._scene_look
    result = {}
    background = look.get("background", {})
    if background.get("op") == "set_background_color":
        result["background"] = {"color": background["color"]}
    elif background.get("mode") in ("light", "dark"):
        result["background"] = {"mode": background["mode"]}
    lighting = look.get("lighting", {})
    values = {key: lighting[key] for key in ("ambient", "diffuse") if key in lighting}
    if values:
        result["lighting"] = values
    return validate_environment(result)


def apply_environment(view, environment):
    if "background" in environment:
        background = environment["background"]
        view.scene.set_background(background.get("color", background.get("mode")), skip_digestion=True)
    if "lighting" in environment:
        view.scene.set_lighting(**deepcopy(environment["lighting"]), skip_digestion=True)
