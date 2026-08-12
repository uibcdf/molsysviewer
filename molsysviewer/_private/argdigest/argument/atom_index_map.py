"""`atom_index_map` is `{old_atom_index: new_atom_index}` for a system edit.

`None` means atom identity and indices are unchanged, which is the common case and must
stay cheap to express.

When given, both sides are checked to be non-negative integers, because this map is what
every piece of viewer-owned state is remapped through — regions, selections, shapes,
annotations, measurements, visibility, per-atom colours. A single bad entry does not
raise: it silently moves a region onto different atoms, and the scene stays plausible.
That is the failure this digester exists to prevent, and it is the reason the check is
worth its cost on a map that may be large.
"""

from collections.abc import Mapping

from molsysviewer._private.exceptions import ArgumentError


def _is_index(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def digest_atom_index_map(atom_index_map, caller=None):
    if atom_index_map is None:
        return None
    if not isinstance(atom_index_map, Mapping):
        raise ArgumentError("atom_index_map", value=atom_index_map, caller=caller,
                            message="expected {old_atom_index: new_atom_index}")
    for old, new in atom_index_map.items():
        if not _is_index(old) or not _is_index(new):
            raise ArgumentError(
                "atom_index_map",
                value={old: new},
                caller=caller,
                message="atom indices are non-negative integers on both sides",
            )
    return dict(atom_index_map)
