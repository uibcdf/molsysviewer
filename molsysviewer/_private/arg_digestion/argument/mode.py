from molsysviewer._private.exceptions import ArgumentError
from ..helpers import normalize_viewer_caller

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
            "molsysviewer.viewer.camera.CameraManager.set_mode",
        }:
            if mode in ["perspective", "orthographic"]:
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
