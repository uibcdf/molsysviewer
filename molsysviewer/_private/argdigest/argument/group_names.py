from ...exceptions import ArgumentError


def digest_group_names(group_names, caller=None):
    if group_names is None:
        return None
    if isinstance(group_names, str):
        group_names = [group_names]
    if isinstance(group_names, (list, tuple)) and all(isinstance(name, str) and name for name in group_names):
        return list(group_names)
    raise ArgumentError("group_names", value=group_names, caller=caller)
