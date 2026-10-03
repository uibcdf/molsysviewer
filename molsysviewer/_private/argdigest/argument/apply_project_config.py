from ...exceptions import ArgumentError


def digest_apply_project_config(apply_project_config, caller=None):
    if isinstance(apply_project_config, bool):
        return apply_project_config
    raise ArgumentError("apply_project_config", value=apply_project_config, caller=caller)
