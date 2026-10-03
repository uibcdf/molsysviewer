from ...exceptions import ArgumentError


def digest_role(role, caller=None):
    if isinstance(role, str) and role.strip():
        return role
    raise ArgumentError("role", value=role, caller=caller)
