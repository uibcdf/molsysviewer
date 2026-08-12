from molsysviewer._private.exceptions import ArgumentError
from ..helpers import normalize_viewer_caller

# `mode` is the most overloaded argument name in this library: five unrelated closed sets,
# told apart only by the caller. File access (auto/read/write), load semantics
# (add/replace/append_structures/auto), camera projection (perspective/orthographic),
# popup surface (canvas/panel) and playback (loop/once/ping-pong).
#
# Each branch must list the caller string ArgDigest actually builds --
# `<owner module>.<function name>`. A class-qualified spelling alone silently disables the
# branch, and every value it was meant to accept is then refused; that is how
# `camera.set_mode` came to raise for both of its valid values.

def digest_mode(mode, caller=None):

    caller = normalize_viewer_caller(caller)

    # `mode` is optional wherever it defaults to None (playback, for instance);
    # the callee applies its own default. Without this, calling such a method
    # without arguments raised instead of running.
    if mode is None:
        return None

    if isinstance(mode, str):
        if caller.startswith('molsysmt.file'):
            if mode in ['auto', 'read', 'write']:
                return mode
        if caller in {
            "molsysviewer.viewer.load",
            "molsysviewer.viewer.MolSysView.load",
        }:
            if mode in ["add", "replace", "append_structures", "auto"]:
                return mode
        if caller in {
            # ArgDigest builds the caller as `<owner module>.<function name>`, so the
            # `CameraManager.` spelling below is never produced. It was the only entry
            # here, which meant `view.camera.set_mode("orthographic")` -- one of its two
            # valid values -- raised. Kept alongside the real one rather than deleted,
            # because a class-qualified caller is what a reader expects to see.
            "molsysviewer.viewer.camera.CameraManager.set_mode",
            "molsysviewer.viewer.camera.set_mode",
            # `scene.set_projection` is the public route to the same setting.
            "molsysviewer.scene.set_projection",
            "molsysviewer.scene.SceneManager.set_projection",
        }:
            if mode in ["perspective", "orthographic"]:
                return mode
        if caller in {
            "molsysviewer.viewer.build_popup_scene_snapshot",
            "molsysviewer.viewer.popup_snapshot.build_popup_scene_snapshot",
        }:
            if mode in ["canvas", "panel"]:
                return mode
        if caller in {
            "molsysviewer.player.play",
            "molsysviewer.player.set_mode",
            # `MolSysView.play()` normalizes to this caller; without it a valid
            # playback mode was rejected from the public entry point.
            "molsysviewer.viewer.play",
            "molsysviewer.viewer.MolSysView.play",
        }:
            if mode in ["loop", "once", "ping-pong"]:
                return mode

    raise ArgumentError('mode', value=mode, caller=caller, message=None)
