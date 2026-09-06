"""`explicit` is a Chromium executable the caller chose instead of one found on the PATH.

`None` asks `find_chromium_executable` to search. A path — `str` or `Path` — asks for that
one file, and the function refuses it if it is not there. Blank is refused here rather
than treated as `None`: it reads as a configuration that resolved to nothing, and falling
back to whatever the PATH offers would silently start a browser the caller did not choose.
"""

from pathlib import Path

from molsysviewer._private.exceptions import ArgumentError


def digest_explicit(explicit, caller=None):
    if explicit is None:
        return None
    if isinstance(explicit, Path):
        return str(explicit)
    if isinstance(explicit, str) and explicit.strip():
        return explicit
    raise ArgumentError("explicit", value=explicit, caller=caller,
                        message="expected a path to a Chromium-family executable, or None "
                                "to search the PATH")
