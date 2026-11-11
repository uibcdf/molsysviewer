from molsysviewer._private.exceptions import ArgumentError


def digest_sample_level(sample_level, caller=None):
    if type(sample_level) is not int or not 0 <= sample_level <= 5:
        raise ArgumentError(
            "sample_level", value=sample_level, caller=caller, message="expected an integer from 0 to 5"
        )
    return sample_level
