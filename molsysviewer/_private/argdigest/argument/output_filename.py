from pathlib import Path

from ...exceptions import ArgumentError


def digest_output_filename(output_filename, caller=None):
    """Validate and normalize an optional output filename.

    Parameters
    ----------
    output_filename : str, pathlib.Path, or None
        Destination filename; native path objects are converted to absolute strings.
    caller : str, optional
        Name of the calling function or method for error reporting.

    Returns
    -------
    str or None
        Normalized filename, or None when no output was requested.

    Raises
    ------
    ArgumentError
        If the value is neither a string, native path, nor None.
    """

    if isinstance(output_filename, Path):
        output_filename = output_filename.absolute().__str__()

    if output_filename is None:
        return output_filename
    elif isinstance(output_filename, str):
        return output_filename

    raise ArgumentError("output_filename", value=output_filename, caller=caller, message=None)
