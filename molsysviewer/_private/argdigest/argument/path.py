from pathlib import Path

from ...exceptions import ArgumentError


def digest_path(path, caller=None):
    if isinstance(path, Path):
        return str(path)
    if isinstance(path, str):
        return path
    raise ArgumentError("path", value=path, caller=caller, message=None)
