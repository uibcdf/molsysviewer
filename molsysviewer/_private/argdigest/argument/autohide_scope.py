from ...exceptions import ArgumentError


def digest_autohide_scope(autohide_scope, caller=None):
    if autohide_scope is None:
        return None
    if isinstance(autohide_scope, str):
        value = autohide_scope.strip().lower()
        if value in ("controls", "canvas"):
            return value
    raise ArgumentError(
        "autohide_scope", value=autohide_scope, caller=caller,
        message='Use "controls" or "canvas".',
    )
