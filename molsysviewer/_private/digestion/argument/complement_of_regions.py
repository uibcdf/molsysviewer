from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._private.variables import is_all


def digest_complement_of_regions(complement_of_regions, caller=None):
    if complement_of_regions is None:
        return None
    if is_all(complement_of_regions):
        return "all"
    if isinstance(complement_of_regions, str):
        return complement_of_regions
    if isinstance(complement_of_regions, (list, tuple)):
        if all(isinstance(ii, str) for ii in complement_of_regions):
            return list(complement_of_regions)
    raise ArgumentError(
        "complement_of_regions",
        value=complement_of_regions,
        caller=caller,
        message=None,
    )
