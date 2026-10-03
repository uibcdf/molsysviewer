from ...exceptions import ArgumentError


def digest_app_argv(app_argv, caller=None):
    if app_argv is None:
        return None
    if isinstance(app_argv, (list, tuple)) and all(isinstance(item, str) for item in app_argv):
        return list(app_argv)
    raise ArgumentError("app_argv", value=app_argv, caller=caller)
