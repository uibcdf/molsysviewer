from ...exceptions import ArgumentError


def digest_workspace(workspace, caller=None):
    if workspace is None and caller in {
        "molsysviewer.viewer.set_workspace_panel",
        "molsysviewer.viewer.MolSysView.set_workspace_panel",
    }:
        return None
    if isinstance(workspace, str):
        workspace = workspace.strip()
        if workspace:
            return workspace
    raise ArgumentError("workspace", value=workspace, caller=caller, message=None)
