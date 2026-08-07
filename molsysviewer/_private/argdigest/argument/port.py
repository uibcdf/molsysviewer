from ...exceptions import ArgumentError


def digest_port(port, caller=None):
    # A port is a TCP port, so the range is not a matter of taste. Below 1024
    # needs privileges a preview server should never ask for.
    if isinstance(port, int) and not isinstance(port, bool) and 1024 <= port <= 65535:
        return port

    raise ArgumentError(
        "port", value=port, caller=caller,
        message="Expected a TCP port between 1024 and 65535.",
    )
