"""`new_molsys` is the molecular system that replaces the view's current one.

Presence is all that is checked. The type is not: `apply_system_edit` is the seam
add-ons use, and what counts as a molecular system is MolSysMT's to decide, not the
viewer's — narrowing it here would reject a form MolSysMT supports and MolSysViewer has
not heard of.

`None` is refused because it is the shape of a mistake rather than a choice: it means an
edit produced nothing and the caller did not notice. The body raised for it already; here
the failure names the caller.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_new_molsys(new_molsys, caller=None):
    if new_molsys is None:
        raise ArgumentError(
            "new_molsys",
            value=new_molsys,
            caller=caller,
            message="applying an edit needs the molecular system it produced",
        )
    return new_molsys
