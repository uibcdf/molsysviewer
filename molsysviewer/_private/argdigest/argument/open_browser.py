from ...exceptions import ArgumentError


def digest_open_browser(open_browser, caller=None):
    if isinstance(open_browser, bool):
        return open_browser

    raise ArgumentError("open_browser", value=open_browser, caller=caller, message=None)
