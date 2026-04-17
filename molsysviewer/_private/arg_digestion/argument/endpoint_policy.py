from molsysviewer._private.exceptions import ArgumentError


_ALLOWED_ENDPOINT_POLICIES = {"atom", "centroid", "representative_atom"}


def digest_endpoint_policy(endpoint_policy, caller=None):
    if endpoint_policy is None:
        return None

    if isinstance(endpoint_policy, str):
        value = endpoint_policy.strip().lower()
        if value in _ALLOWED_ENDPOINT_POLICIES:
            return value

    raise ArgumentError("endpoint_policy", value=endpoint_policy, caller=caller, message=None)
