"""`demo_key` names the demo system a reference add-on builds its view from.

Checked against the live catalogue rather than a hardcoded list, so adding a demo does not
require editing this file and removing one cannot leave a stale name looking valid.

The failure it prevents is a `KeyError` from inside `demo[...]`, which names the catalogue
and not the argument that reached it.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_demo_key(demo_key, caller=None):
    if demo_key is None:
        return None
    from molsysviewer.demo import demo

    if demo_key in demo:
        return demo_key
    raise ArgumentError(
        "demo_key",
        value=demo_key,
        caller=caller,
        message=f"unknown demo system; available: {', '.join(sorted(demo))}",
    )
