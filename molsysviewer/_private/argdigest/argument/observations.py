"""Per-series optional producer records; content is shared with state validation."""

from molsysviewer._private.exceptions import ArgumentError


def digest_observations(observations, caller=None):
    if observations is None:
        return None
    if not isinstance(observations, (list, tuple)) or any(
        item is not None and type(item) is not dict for item in observations
    ):
        raise ArgumentError(
            "observations",
            value=observations,
            caller=caller,
            message="Use one optional producer JSON object per plot series.",
        )
    return observations
