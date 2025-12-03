# molsysviewer/loaders/load_from_url.py

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..viewer import MolSysView


def ensure_view(view: "MolSysView" | None = None) -> "MolSysView":
    view = ensure_view(view)
    return view


def load_from_url(
    url: str,
    *,
    format: str | None = None,
    label: str | None = None,
    view: "MolSysView" | None = None,
) -> "MolSysView":
    """Backend interno para MolSysView.load_from_url(...).

    De momento:
    - delega totalmente el parseo de la URL al frontend (Mol*),
    - deja `_molsys` y `atom_mask` a None (no hay operaciones de selección).
    """

    if view is None:
        from ..viewer import MolSysView
        view = MolSysView()

    view.molecular_system = url
    view.selection = "all"
    view.structure_indices = "all"
    view._molsys = None
    view.atom_mask = None
    view.structure_mask = None

    view._send(
        {
            "op": "load_structure_from_url",
            "url": url,
            "format": format,
            "label": label,
        }
    )

    return view


# Compatibilidad hacia atrás
load_url = load_from_url
