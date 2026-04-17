from molsysviewer._private.exceptions import ArgumentError
from ..helpers import normalize_viewer_caller

def digest_mode(mode, caller=None):

    caller = normalize_viewer_caller(caller)

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
            "molsysviewer.viewer.write_html",
            "molsysviewer.viewer.MolSysView.write_html",
            "molsysviewer.exports.html",
            "molsysviewer.exports.ExportManager.html",
        }:
            if mode in ["standalone", "lite"]:
                return mode
        if caller in {
            "molsysviewer.viewer.camera.CameraManager.set_mode",
        }:
            if mode in ["perspective", "orthographic"]:
                return mode
        if caller in {
            "molsysviewer.player.play",
            "molsysviewer.player.set_mode",
        }:
            if mode in ["loop", "once", "ping-pong"]:
                return mode

    raise ArgumentError('mode', value=mode, caller=caller, message=None)
