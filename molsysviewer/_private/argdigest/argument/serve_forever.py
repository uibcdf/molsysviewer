from ...exceptions import ArgumentError


def digest_serve_forever(serve_forever, caller=None):
    if isinstance(serve_forever, bool):
        return serve_forever

    raise ArgumentError("serve_forever", value=serve_forever, caller=caller, message=None)
