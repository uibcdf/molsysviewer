from os import PathLike, fspath

from ...exceptions import ArgumentError


def digest_filename(filename, caller=None):

    if caller and caller.startswith("molsysviewer.interactions.") and isinstance(filename, PathLike):
        return fspath(filename)

    if isinstance(filename, str):
        return filename

    raise ArgumentError("filename", value=filename, caller=caller, message=None)
