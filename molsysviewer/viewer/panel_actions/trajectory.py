from __future__ import annotations

from typing import Any, Mapping


def _integer(content: Mapping[str, Any], key: str) -> int:
    value = content.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"trajectory action requires integer {key}.")
    return value


def set_trajectory_frame(view: Any, content: Mapping[str, Any]) -> None:
    index = _integer(content, "index")
    if index < 0 or index >= view.player.n_structures:
        raise ValueError("trajectory frame index is outside the loaded trajectory.")
    view.player.go_to_structure(index, skip_digestion=True)


def step_trajectory(view: Any, content: Mapping[str, Any]) -> None:
    by = _integer(content, "by")
    if by == 0:
        raise ValueError("step_trajectory requires non-zero by.")
    if by > 0:
        view.player.step_forward(by, skip_digestion=True)
    else:
        view.player.step_backward(-by, skip_digestion=True)


def set_trajectory_playback(view: Any, content: Mapping[str, Any]) -> None:
    action = content.get("playback_action")
    if action == "stop":
        view.player.pause(skip_digestion=True)
        return
    if action != "play":
        raise ValueError("set_trajectory_playback requires playback_action 'play' or 'stop'.")

    kwargs: dict[str, Any] = {}
    if "fps" in content:
        kwargs["fps"] = _integer(content, "fps")
        if kwargs["fps"] < 1:
            raise ValueError("trajectory playback fps must be positive.")
    if "step" in content:
        kwargs["step_size"] = _integer(content, "step")
        if kwargs["step_size"] < 1:
            raise ValueError("trajectory playback step must be positive.")
    if "mode" in content:
        mode = content.get("mode")
        if mode not in {"loop", "once", "ping-pong"}:
            raise ValueError("trajectory playback mode must be 'loop', 'once', or 'ping-pong'.")
        kwargs["mode"] = mode
    if "direction" in content:
        direction = content.get("direction")
        if direction not in {"forward", "backward"}:
            raise ValueError("trajectory playback direction must be 'forward' or 'backward'.")
        kwargs["direction"] = direction
    view.player.play(skip_digestion=True, **kwargs)


HANDLERS = {
    "set_trajectory_frame": set_trajectory_frame,
    "step_trajectory": step_trajectory,
    "set_trajectory_playback": set_trajectory_playback,
}
