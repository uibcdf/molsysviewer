from ...exceptions import ArgumentError


def digest_show_empty_host_overlay(show_empty_host_overlay, caller=None):
    if isinstance(show_empty_host_overlay, bool):
        return show_empty_host_overlay
    raise ArgumentError("show_empty_host_overlay", value=show_empty_host_overlay, caller=caller)
