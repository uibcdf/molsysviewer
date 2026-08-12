"""`molsys` is the molecular system a colour expansion reads its elements from.

Presence only, for the same reason as `new_molsys`: what counts as a molecular system is
MolSysMT's to decide, and narrowing it here would refuse a form MolSysMT supports and
MolSysViewer has not heard of.

`expand_values_to_atoms` is a module-level helper rather than a view method, so it has no
loaded system to fall back on — `None` here is not "use the current one", it is a caller
who lost track of theirs.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_molsys(molsys, caller=None):
    if molsys is None:
        raise ArgumentError(
            "molsys",
            value=molsys,
            caller=caller,
            message="expanding values to atoms needs the system they belong to",
        )
    return molsys
