from os import PathLike
from pathlib import Path

from molsysviewer._private.exceptions import ArgumentError


def _normalize_paths(molecular_system):
    if isinstance(molecular_system, PathLike):
        return str(Path(molecular_system).absolute())
    if isinstance(molecular_system, list):
        return [_normalize_paths(item) for item in molecular_system]
    if isinstance(molecular_system, tuple):
        return tuple(_normalize_paths(item) for item in molecular_system)
    return molecular_system


def digest_molecular_system(molecular_system, caller=None):
    """Check if an object is a molecular system.

    Parameters
    ----------
    molecular_system : Any
        The molecular system object to be checked.
    caller: str, optional
        Name of the function or method that is being digested.

    Returns
    -------
    molecular_system : Any
        The molecular system object.

    Raises
    ------
    MolecularSystemNeededError
        If the given object is not a molecular system.
    """
    from molsysmt.basic import are_multiple_molecular_systems, is_a_molecular_system, merge

    molecular_system = _normalize_paths(molecular_system)

    if caller in ["molsysviewer.new_view.new_view", "molsysviewer.loaders.load_molsysmt.load_from_molsysmt"]:
        return molecular_system

    if caller == "molsysmt.basic.view.view":
        if is_a_molecular_system(molecular_system):
            return molecular_system
        elif are_multiple_molecular_systems(molecular_system):
            return merge(molecular_system, to_form="molsysmt.MolSys")

    if is_a_molecular_system(molecular_system):
        return molecular_system

    raise ArgumentError("molecular_system", value=molecular_system, caller=caller, message=None)
