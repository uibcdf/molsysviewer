from pathlib import Path

from ...exceptions import ArgumentError


def digest_output_directory(output_directory, caller=None):
    if isinstance(output_directory, Path):
        return str(output_directory)
    if isinstance(output_directory, str) and output_directory:
        return output_directory
    raise ArgumentError("output_directory", value=output_directory, caller=caller, message=None)
