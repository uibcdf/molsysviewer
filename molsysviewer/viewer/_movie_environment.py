"""The bounded, renderer-observed Movie environment and its declared intent."""

from copy import deepcopy

from .._scene_environment import validate_environment
from .frontend_requests import FrontendRequestError


def resolved_environment(value):
    environment = validate_environment(value)
    if (
        set(environment) != {"background", "lighting"}
        or set(environment["background"]) != {"color"}
        or set(environment["lighting"]) != {"ambient", "diffuse"}
    ):
        raise ValueError("Movie environment capture requires RGB background and both lighting intensities.")
    return environment


def environment_capture(value, environment):
    if not isinstance(value, dict) or set(value) != {"version", "intent"}:
        raise ValueError("Invalid Movie environment capture record.")
    if type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("Unsupported Movie environment capture version.")
    resolved_environment(environment)
    return {"version": 1, "intent": validate_environment(value["intent"])}


def require_environment_capture(view):
    versions = view._frontend_capabilities.get("movie_environment_capture", [])
    if not isinstance(versions, (list, tuple)) or not any(
        type(version) is int and version == 1 for version in versions
    ):
        raise FrontendRequestError(reason="movie_environment_capture_not_supported")


def finish_environment_capture(view, captured, reply):
    from .visual_capture import finish_live_capture

    if type(reply.get("movie_environment_capture")) is not int or reply["movie_environment_capture"] != 1:
        raise FrontendRequestError(reason="invalid_movie_environment_capture")
    try:
        environment = resolved_environment(reply.get("movie_environment"))
    except (ValueError, TypeError) as error:
        raise FrontendRequestError(reason="invalid_movie_environment_capture") from error
    metadata = {"version": 1, "intent": deepcopy(captured.state.get("environment", {}))}
    scene = finish_live_capture(view, captured, reply).state
    scene["environment"] = environment
    return metadata


def comparable_scene(timeline, scene):
    """Allow the original declared intent or the actual captured values, never other edits."""
    baseline = timeline._data["baseline"]
    capture = baseline.get("environment_capture")
    if capture is None:
        return scene
    scene = deepcopy(scene)
    environment = scene.setdefault("environment", {})
    for prop, value in baseline["scene"]["environment"].items():
        if environment.get(prop) == capture["intent"].get(prop):
            environment[prop] = deepcopy(value)
    return scene
