from molsysviewer._private.exceptions import ArgumentError


def digest_n(n, caller=None):
    try:
        v = int(n)
        if v >= 0:
            return v
    except (TypeError, ValueError):
        pass
    raise ArgumentError('n', value=n, caller=caller, message=None)
