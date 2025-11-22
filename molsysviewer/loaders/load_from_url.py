# molsysviewer/loaders/load_from_url.py

from __future__ import annotations

from typing import Any


def load_from_url(
    view: Any,
    *,
    url: str,
    format: str | None = None,
    label: str | None = None,
) -> None:
    """Backend interno para MolSysView.load_from_url(...).

    De momento:
    - delega totalmente el parseo de la URL al frontend (Mol*),
    - deja `_molsys` y `atom_mask` a None (no hay operaciones de selección).
    """

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

