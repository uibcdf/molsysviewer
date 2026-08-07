from ...exceptions import ArgumentError
from ..helpers import normalize_viewer_caller


def digest_panel(panel, caller=None):
    caller = normalize_viewer_caller(caller)
    if panel is None:
        return None
    if isinstance(panel, str) and caller in {
        "molsysviewer.viewer.set_panel_mode",
        "molsysviewer.viewer.MolSysView.set_panel_mode",
    }:
        if panel in {"navigate", "addons"}:
            return panel
    if isinstance(panel, str) and caller in {
        "molsysviewer.viewer.set_workspace_panel",
        "molsysviewer.viewer.MolSysView.set_workspace_panel",
    }:
        panel = panel.strip()
        if panel:
            return panel
    raise ArgumentError("panel", value=panel, caller=caller, message=None)
