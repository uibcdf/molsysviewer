from molsysviewer._private.exceptions import ArgumentError


def digest_views(views, caller=None):
    """Validate a sequence of MolSysView instances."""
    from molsysviewer.viewer import MolSysView

    if not isinstance(views, (list, tuple)) or len(views) == 0:
        raise ArgumentError("views", value=views, caller=caller, message=None)

    if not all(isinstance(view, MolSysView) for view in views):
        raise ArgumentError("views", value=views, caller=caller, message=None)

    return list(views)
