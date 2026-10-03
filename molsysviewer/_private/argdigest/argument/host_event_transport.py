from ...exceptions import ArgumentError


def digest_host_event_transport(host_event_transport, caller=None):
    if host_event_transport is None or isinstance(host_event_transport, str):
        return host_event_transport
    raise ArgumentError("host_event_transport", value=host_event_transport, caller=caller)
