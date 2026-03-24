from ...exceptions import ArgumentError


def digest_workspace(workspace, caller=None):
    if isinstance(workspace, str):
        workspace = workspace.strip()
        if workspace:
            return workspace
    raise ArgumentError("workspace", value=workspace, caller=caller, message=None)
