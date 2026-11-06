from ...exceptions import ArgumentError


def digest_expected_target(expected_target, caller=None):
    """Preserve the exact primary-object reference, without conversion or copying."""
    if expected_target is None:
        return None
    from molsysmt.native import MolSys

    if isinstance(expected_target, MolSys):
        return expected_target
    raise ArgumentError("expected_target", value=expected_target, caller=caller)
