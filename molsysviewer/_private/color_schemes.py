"""Structural color-scheme registry and name resolution.

This lives apart from ``molsysviewer.styles`` on purpose: it is pure data plus a
lookup, and argument digesters need it. Importing ``styles`` pulls in
``viewer.presets`` → ``viewer.core`` → ``styles`` again, so a digester importing
it directly would break whenever it is the first module loaded.
"""

from __future__ import annotations

from typing import Any

STRUCTURAL_COLOR_SCHEMES: dict[str, dict[str, Any]] = {
    "element_cpk": {
        "molstar_theme": "element-symbol",
        "description": "Color by element using a CPK-like palette.",
    },
    "secondary_structure_default": {
        "molstar_theme": "secondary-structure",
        "description": "Color polymers by secondary-structure class.",
    },
    "chain_default": {
        "molstar_theme": "chain-id",
        "description": "Color polymers by chain identifier.",
    },
    "physicochemical": {
        "molstar_theme": "msv-physicochemical",
        "description": "Color by residue physicochemical properties.",
    },
    "group_name": {
        "molstar_theme": "residue-name",
        "description": "Color by group name (amino-acid residue, water, ion, ligand, …).",
    },
    "molecule_type": {
        "molstar_theme": "molecule-type",
        "description": "Color by molecule class such as protein, RNA, DNA, ion, or water.",
    },
    "entity_default": {
        "molstar_theme": "entity-id",
        "description": "Color by entity identifier.",
    },
    "illustrative_default": {
        "molstar_theme": "illustrative",
        "description": "Use Mol* illustrative coloring.",
    },
}


# Alternative spellings accepted for convenience. Two sources:
#
# - MolSysMT attribute names, since users of the ecosystem naturally write
#   `chain_id` rather than `chain_default`.
# - `residue_name`, tolerated for people used to the PDB/Mol* wording. The
#   MolSysSuite term is `group_name`, which is the canonical tag: `residue_name`
#   must not be used in examples, docs or the cookbook.
#
# Mol* theme names (`chain-id`, `element-symbol`, …) are *not* listed here: they
# are derived from the `molstar_theme` field of STRUCTURAL_COLOR_SCHEMES itself,
# so the two never drift apart.
MOLSYSMT_COLOR_SCHEME_ALIASES: dict[str, str] = {
    "chain_id": "chain_default",
    "chain_name": "chain_default",
    "residue_name": "group_name",
    "entity_id": "entity_default",
    "entity_name": "entity_default",
    "element": "element_cpk",
}


def _molstar_color_scheme_aliases() -> dict[str, str]:
    return {
        entry["molstar_theme"]: tag
        for tag, entry in STRUCTURAL_COLOR_SCHEMES.items()
        if isinstance(entry.get("molstar_theme"), str)
    }


def resolve_structural_color_scheme(scheme: Any) -> str | None:
    """Resolve a structural color-scheme name to its canonical tag.

    Accepts the canonical tags (``chain_default``…), the underlying Mol* theme
    names (``chain-id``…), and MolSysMT attribute names (``chain_id``…).
    Returns ``None`` when the name is not recognized, so callers can raise with
    the list of valid options instead of silently doing nothing.
    """
    if not isinstance(scheme, str):
        return None
    normalized = scheme.strip()
    if not normalized:
        return None
    if normalized in STRUCTURAL_COLOR_SCHEMES:
        return normalized
    molstar = _molstar_color_scheme_aliases()
    if normalized in molstar:
        return molstar[normalized]
    return MOLSYSMT_COLOR_SCHEME_ALIASES.get(normalized)


__all__ = [
    "MOLSYSMT_COLOR_SCHEME_ALIASES",
    "STRUCTURAL_COLOR_SCHEMES",
    "resolve_structural_color_scheme",
]
