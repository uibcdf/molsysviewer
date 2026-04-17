from __future__ import annotations

REPRESENTATION_ALIASES = {
    # ball-and-stick family
    "sticks": "ball-and-stick",
    "ball_and_stick": "ball-and-stick",
    "ballstick": "ball-and-stick",
    "licorice": "ball-and-stick",   # licorice = cylinders, which is ball-and-stick in Mol*
    "cylinders": "ball-and-stick",
    # line family
    "lines": "line",
    "wire": "line",
    "wireframe": "line",
    # other aliases
    "ribbon": "backbone",
    "surface": "molecular-surface",
    "vdw": "spacefill",
    "dots": "point",
}

# Molecular-system representations exposed in the public Python API.
# These map 1:1 to Mol* built-in structure representation types.
# Not included:
#   "label"       → use view.annotations.add_annotation() instead
#   "orientation" → structural axes helper; use molstar_repr_type escape hatch if needed
#   "plane"       → best-fit plane helper; use molstar_repr_type escape hatch if needed
ALLOWED_REPRESENTATIONS = {
    "cartoon",
    "backbone",
    "ball-and-stick",
    "carbohydrate",
    "ellipsoid",
    "gaussian-surface",
    "gaussian-volume",
    "line",
    "molecular-surface",
    "point",
    "putty",
    "spacefill",
}

COMMON_REPRESENTATION_PARAMS = [
    {
        "name": "alpha",
        "kind": "number",
        "description": "Opacity in the [0, 1] range.",
    },
    {
        "name": "quality",
        "kind": "enum",
        "values": ["auto", "lowest", "lower", "low", "medium", "high", "higher", "highest", "custom"],
        "description": "Rendering quality preset.",
    },
    {
        "name": "color_scheme",
        "kind": "string",
        "description": "Curated MolSysViewer structural color scheme.",
    },
    {
        "name": "size_scheme",
        "kind": "string",
        "description": "Curated MolSysViewer structural size scheme.",
    },
    {
        "name": "molstar_color_theme",
        "kind": "string-or-dict",
        "description": "Advanced Mol* color theme escape hatch.",
    },
    {
        "name": "molstar_size_theme",
        "kind": "string-or-dict",
        "description": "Advanced Mol* size theme escape hatch.",
    },
]

REPRESENTATION_PARAM_SCHEMAS = {
    "cartoon": {
        "summary": "Polymer cartoon representation.",
        "specific_params": [
            {"name": "sizeFactor", "kind": "number"},
            {"name": "tubularHelices", "kind": "boolean"},
            {"name": "helixProfile", "kind": "enum", "values": ["square", "elliptical", "rounded"]},
            {"name": "nucleicProfile", "kind": "enum", "values": ["square", "elliptical", "rounded"]},
        ],
    },
    "backbone": {
        "summary": "Backbone cylinders and spheres.",
        "specific_params": [
            {"name": "sizeFactor", "kind": "number"},
            {"name": "sizeAspectRatio", "kind": "number"},
        ],
    },
    "ball-and-stick": {
        "summary": "Atomic detail with bonds.",
        "specific_params": [
            {"name": "sizeFactor", "kind": "number"},
            {"name": "sizeAspectRatio", "kind": "number"},
            {"name": "ignoreHydrogens", "kind": "boolean"},
            {"name": "ignoreHydrogensVariant", "kind": "enum", "values": ["all", "non-polar"]},
            {"name": "multipleBonds", "kind": "enum", "values": ["off", "offset", "symmetric"]},
        ],
    },
    "carbohydrate": {
        "summary": "Carbohydrate symbols and links.",
        "specific_params": [
            {"name": "sizeFactor", "kind": "number"},
            {"name": "terminalLinkSizeFactor", "kind": "number"},
        ],
    },
    "ellipsoid": {
        "summary": "Anisotropic displacement ellipsoids.",
        "specific_params": [
            {"name": "sizeFactor", "kind": "number"},
        ],
    },
    "gaussian-surface": {
        "summary": "Gaussian molecular surface.",
        "specific_params": [
            {"name": "resolution", "kind": "number"},
            {"name": "ignoreHydrogens", "kind": "boolean"},
        ],
    },
    "gaussian-volume": {
        "summary": "Gaussian volume representation.",
        "specific_params": [
            {"name": "resolution", "kind": "number"},
            {"name": "ignoreHydrogens", "kind": "boolean"},
        ],
    },
    "line": {
        "summary": "Wireframe or licorice-style line rendering.",
        "specific_params": [
            {"name": "sizeFactor", "kind": "number"},
            {"name": "ignoreHydrogens", "kind": "boolean"},
            {"name": "ignoreHydrogensVariant", "kind": "enum", "values": ["all", "non-polar"]},
            {"name": "multipleBonds", "kind": "enum", "values": ["off", "offset", "symmetric"]},
        ],
    },
    "molecular-surface": {
        "summary": "Solvent-accessible molecular surface.",
        "specific_params": [
            {"name": "probeRadius", "kind": "number"},
            {"name": "resolution", "kind": "number"},
            {"name": "ignoreHydrogens", "kind": "boolean"},
        ],
    },
    "point": {
        "summary": "Point-based atomic representation.",
        "specific_params": [
            {"name": "sizeFactor", "kind": "number"},
            {"name": "ignoreHydrogens", "kind": "boolean"},
            {"name": "ignoreHydrogensVariant", "kind": "enum", "values": ["all", "non-polar"]},
        ],
    },
    "putty": {
        "summary": "Tube whose radius varies along the polymer.",
        "specific_params": [
            {"name": "sizeFactor", "kind": "number"},
            {"name": "sizeAspectRatio", "kind": "number"},
        ],
    },
    "spacefill": {
        "summary": "Van der Waals spheres.",
        "specific_params": [
            {"name": "sizeFactor", "kind": "number"},
            {"name": "ignoreHydrogens", "kind": "boolean"},
            {"name": "ignoreHydrogensVariant", "kind": "enum", "values": ["all", "non-polar"]},
        ],
    },
}


def normalize_representation_type(value: str | None) -> str | None:
    if value is None:
        return None
    key = value.replace("_", "-").lower().strip()
    key = REPRESENTATION_ALIASES.get(key, key)
    if key not in ALLOWED_REPRESENTATIONS:
        raise ValueError(
            f"Unsupported representation type '{value}'. Allowed: {sorted(ALLOWED_REPRESENTATIONS)}"
        )
    return key


__all__ = [
    "ALLOWED_REPRESENTATIONS",
    "COMMON_REPRESENTATION_PARAMS",
    "REPRESENTATION_ALIASES",
    "REPRESENTATION_PARAM_SCHEMAS",
    "normalize_representation_type",
]
