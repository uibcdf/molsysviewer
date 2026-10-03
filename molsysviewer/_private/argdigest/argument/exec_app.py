from ...exceptions import ArgumentError


def digest_exec_app(exec_app, caller=None):
    if isinstance(exec_app, bool):
        return exec_app
    raise ArgumentError("exec_app", value=exec_app, caller=caller)
