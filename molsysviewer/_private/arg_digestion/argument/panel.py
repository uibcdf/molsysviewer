from ...exceptions import ArgumentError


def digest_panel(panel, caller=None):
    if panel is None:
        return None
    if isinstance(panel, str) and caller in {
        "molsysviewer.viewer.set_panel_mode",
        "molsysviewer.viewer.MolSysView.set_panel_mode",
    }:
        if panel in {"navigate", "workbench"}:
            return panel
    raise ArgumentError("panel", value=panel, caller=caller, message=None)

