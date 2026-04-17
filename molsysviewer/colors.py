from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


MOLSTAR_COLOR_NAMES: dict[str, int] = {
    "aliceblue": 0xF0F8FF,
    "antiquewhite": 0xFAEBD7,
    "aqua": 0x00FFFF,
    "aquamarine": 0x7FFFD4,
    "azure": 0xF0FFFF,
    "beige": 0xF5F5DC,
    "bisque": 0xFFE4C4,
    "black": 0x000000,
    "blanchedalmond": 0xFFEBCD,
    "blue": 0x0000FF,
    "blueviolet": 0x8A2BE2,
    "brown": 0xA52A2A,
    "burlywood": 0xDEB887,
    "cadetblue": 0x5F9EA0,
    "chartreuse": 0x7FFF00,
    "chocolate": 0xD2691E,
    "coral": 0xFF7F50,
    "cornflower": 0x6495ED,
    "cornflowerblue": 0x6495ED,
    "cornsilk": 0xFFF8DC,
    "crimson": 0xDC143C,
    "cyan": 0x00FFFF,
    "darkblue": 0x00008B,
    "darkcyan": 0x008B8B,
    "darkgoldenrod": 0xB8860B,
    "darkgray": 0xA9A9A9,
    "darkgreen": 0x006400,
    "darkgrey": 0xA9A9A9,
    "darkkhaki": 0xBDB76B,
    "darkmagenta": 0x8B008B,
    "darkolivegreen": 0x556B2F,
    "darkorange": 0xFF8C00,
    "darkorchid": 0x9932CC,
    "darkred": 0x8B0000,
    "darksalmon": 0xE9967A,
    "darkseagreen": 0x8FBC8F,
    "darkslateblue": 0x483D8B,
    "darkslategray": 0x2F4F4F,
    "darkslategrey": 0x2F4F4F,
    "darkturquoise": 0x00CED1,
    "darkviolet": 0x9400D3,
    "deeppink": 0xFF1493,
    "deepskyblue": 0x00BFFF,
    "dimgray": 0x696969,
    "dimgrey": 0x696969,
    "dodgerblue": 0x1E90FF,
    "firebrick": 0xB22222,
    "floralwhite": 0xFFFAF0,
    "forestgreen": 0x228B22,
    "fuchsia": 0xFF00FF,
    "gainsboro": 0xDCDCDC,
    "ghostwhite": 0xF8F8FF,
    "gold": 0xFFD700,
    "goldenrod": 0xDAA520,
    "gray": 0x808080,
    "green": 0x008000,
    "greenyellow": 0xADFF2F,
    "grey": 0x808080,
    "honeydew": 0xF0FFF0,
    "hotpink": 0xFF69B4,
    "indianred": 0xCD5C5C,
    "indigo": 0x4B0082,
    "ivory": 0xFFFFF0,
    "khaki": 0xF0E68C,
    "laserlemon": 0xFFFF54,
    "lavender": 0xE6E6FA,
    "lavenderblush": 0xFFF0F5,
    "lawngreen": 0x7CFC00,
    "lemonchiffon": 0xFFFACD,
    "lightblue": 0xADD8E6,
    "lightcoral": 0xF08080,
    "lightcyan": 0xE0FFFF,
    "lightgoldenrod": 0xFAFAD2,
    "lightgoldenrodyellow": 0xFAFAD2,
    "lightgray": 0xD3D3D3,
    "lightgreen": 0x90EE90,
    "lightgrey": 0xD3D3D3,
    "lightpink": 0xFFB6C1,
    "lightsalmon": 0xFFA07A,
    "lightseagreen": 0x20B2AA,
    "lightskyblue": 0x87CEFA,
    "lightslategray": 0x778899,
    "lightslategrey": 0x778899,
    "lightsteelblue": 0xB0C4DE,
    "lightyellow": 0xFFFFE0,
    "lime": 0x00FF00,
    "limegreen": 0x32CD32,
    "linen": 0xFAF0E6,
    "magenta": 0xFF00FF,
    "maroon": 0x800000,
    "maroon2": 0x7F0000,
    "maroon3": 0xB03060,
    "mediumaquamarine": 0x66CDAA,
    "mediumblue": 0x0000CD,
    "mediumorchid": 0xBA55D3,
    "mediumpurple": 0x9370DB,
    "mediumseagreen": 0x3CB371,
    "mediumslateblue": 0x7B68EE,
    "mediumspringgreen": 0x00FA9A,
    "mediumturquoise": 0x48D1CC,
    "mediumvioletred": 0xC71585,
    "midnightblue": 0x191970,
    "mintcream": 0xF5FFFA,
    "mistyrose": 0xFFE4E1,
    "moccasin": 0xFFE4B5,
    "navajowhite": 0xFFDEAD,
    "navy": 0x000080,
    "oldlace": 0xFDF5E6,
    "olive": 0x808000,
    "olivedrab": 0x6B8E23,
    "orange": 0xFFA500,
    "orangered": 0xFF4500,
    "orchid": 0xDA70D6,
    "palegoldenrod": 0xEEE8AA,
    "palegreen": 0x98FB98,
    "paleturquoise": 0xAFEEEE,
    "palevioletred": 0xDB7093,
    "papayawhip": 0xFFEFD5,
    "peachpuff": 0xFFDAB9,
    "peru": 0xCD853F,
    "pink": 0xFFC0CB,
    "plum": 0xDDA0DD,
    "powderblue": 0xB0E0E6,
    "purple": 0x800080,
    "purple2": 0x7F007F,
    "purple3": 0xA020F0,
    "rebeccapurple": 0x663399,
    "red": 0xFF0000,
    "rosybrown": 0xBC8F8F,
    "royalblue": 0x4169E1,
    "saddlebrown": 0x8B4513,
    "salmon": 0xFA8072,
    "sandybrown": 0xF4A460,
    "seagreen": 0x2E8B57,
    "seashell": 0xFFF5EE,
    "sienna": 0xA0522D,
    "silver": 0xC0C0C0,
    "skyblue": 0x87CEEB,
    "slateblue": 0x6A5ACD,
    "slategray": 0x708090,
    "slategrey": 0x708090,
    "snow": 0xFFFAFA,
    "springgreen": 0x00FF7F,
    "steelblue": 0x4682B4,
    "tan": 0xD2B48C,
    "teal": 0x008080,
    "thistle": 0xD8BFD8,
    "tomato": 0xFF6347,
    "turquoise": 0x40E0D0,
    "violet": 0xEE82EE,
    "wheat": 0xF5DEB3,
    "white": 0xFFFFFF,
    "whitesmoke": 0xF5F5F5,
    "yellow": 0xFFFF00,
    "yellowgreen": 0x9ACD32,
}


def _normalize_name_token(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


_MOLSTAR_COLOR_NAME_LOOKUP = {_normalize_name_token(name): value for name, value in MOLSTAR_COLOR_NAMES.items()}


@dataclass(frozen=True)
class ContinuousPalette:
    name: str | None
    colors: list[int]
    source: str = "custom"


@dataclass(frozen=True)
class CategoricalColorScheme:
    name: str | None
    mapping: dict[str, int]
    fallback: int | None = None
    source: str = "custom"


def _clamp_channel(value: float) -> int:
    return max(0, min(255, int(round(value))))


def _rgb_to_int(rgb: Sequence[float | int]) -> int:
    if len(rgb) not in (3, 4):
        raise ValueError("RGB colors must have 3 or 4 channels.")
    channels = list(rgb[:3])
    if all(isinstance(item, int) and not isinstance(item, bool) for item in channels):
        red, green, blue = (_clamp_channel(int(item)) for item in channels)
    else:
        red, green, blue = (_clamp_channel(float(item) * 255.0) for item in channels)
    return (red << 16) | (green << 8) | blue


def _parse_hex_color(text: str) -> int | None:
    value = text.strip()
    if not value.startswith("#"):
        return None
    token = value[1:]
    if len(token) == 3:
        token = "".join(ch * 2 for ch in token)
    if len(token) != 6:
        return None
    try:
        return int(token, 16)
    except ValueError:
        return None


def _try_matplotlib_rgba(color: Any) -> tuple[float, float, float, float] | None:
    try:
        import matplotlib.colors as mcolors
    except Exception:
        return None
    try:
        return tuple(float(item) for item in mcolors.to_rgba(color))
    except Exception:
        return None


def normalize_color(color: Any) -> int:
    if isinstance(color, int) and not isinstance(color, bool):
        if 0 <= color <= 0xFFFFFF:
            return color
        raise ValueError(f"Color integer {color!r} is out of RGB range.")

    if isinstance(color, str):
        hex_value = _parse_hex_color(color)
        if hex_value is not None:
            return hex_value
        normalized_name = _normalize_name_token(color)
        if normalized_name in _MOLSTAR_COLOR_NAME_LOOKUP:
            return _MOLSTAR_COLOR_NAME_LOOKUP[normalized_name]
        rgba = _try_matplotlib_rgba(color)
        if rgba is not None:
            return _rgb_to_int(rgba[:3])
        raise ValueError(f"Unknown color name {color!r}.")

    if isinstance(color, (list, tuple)):
        try:
            return _rgb_to_int(color)
        except Exception as exc:
            raise ValueError(f"Unsupported RGB color {color!r}.") from exc

    rgba = _try_matplotlib_rgba(color)
    if rgba is not None:
        return _rgb_to_int(rgba[:3])

    raise ValueError(f"Unsupported color value {color!r}.")


def normalize_colors(colors: Iterable[Any]) -> list[int]:
    return [normalize_color(color) for color in colors]


class ColorRegistry:
    def __init__(self) -> None:
        self._named_colors = dict(MOLSTAR_COLOR_NAMES)
        self._palettes: dict[str, ContinuousPalette] = {}
        self._schemes: dict[str, CategoricalColorScheme] = {}
        self._generated_scheme_palettes: dict[str, tuple[Any, int | None]] = {}

    def color_names(self) -> list[str]:
        return sorted(self._named_colors.keys())

    def normalize_color(self, color: Any) -> int:
        return normalize_color(color)

    def normalize_colors(self, values: Iterable[Any]) -> list[int]:
        return normalize_colors(values)

    def palette_names(self) -> list[str]:
        return sorted(self._palettes.keys())

    def scheme_names(self) -> list[str]:
        return sorted(set(self._schemes.keys()) | set(self._generated_scheme_palettes.keys()))

    def get_palette(self, name: str) -> ContinuousPalette:
        return self._palettes[name]

    def get_scheme(
        self,
        name: str,
        *,
        categories: Sequence[Any] | None = None,
    ) -> CategoricalColorScheme:
        if name in self._schemes:
            return self._schemes[name]
        if name in self._generated_scheme_palettes:
            if categories is None:
                raise ValueError(f"Color scheme {name!r} requires explicit categories.")
            return self.resolve_scheme(name, categories=categories)
        raise KeyError(name)

    def resolve_palette(self, palette: Any, *, samples: int = 256) -> ContinuousPalette:
        if isinstance(palette, ContinuousPalette):
            return palette
        if isinstance(palette, str):
            if palette in self._palettes:
                return self._palettes[palette]
            return self._palette_from_name_or_matplotlib(palette, samples=samples)
        return self._palette_from_matplotlib_or_sequence(palette, samples=samples)

    def register_palette(self, name: str, palette: Any, *, samples: int = 256, overwrite: bool = False) -> ContinuousPalette:
        key = str(name).strip()
        if key == "":
            raise ValueError("Palette name must be a non-empty string.")
        if key in self._palettes and not overwrite:
            raise ValueError(f"Palette {key!r} already exists.")
        resolved = self.resolve_palette(palette, samples=samples)
        stored = ContinuousPalette(name=key, colors=list(resolved.colors), source=resolved.source)
        self._palettes[key] = stored
        return stored

    def resolve_scheme(
        self,
        scheme: Any,
        *,
        categories: Sequence[Any] | None = None,
        fallback: Any | None = None,
    ) -> CategoricalColorScheme:
        if isinstance(scheme, CategoricalColorScheme):
            return scheme
        if isinstance(scheme, str) and scheme in self._schemes:
            return self._schemes[scheme]
        if isinstance(scheme, str) and scheme in self._generated_scheme_palettes:
            if categories is None:
                raise ValueError(f"Color scheme {scheme!r} requires explicit categories.")
            palette_source, generated_fallback = self._generated_scheme_palettes[scheme]
            palette = self.resolve_palette(palette_source, samples=max(len(categories), 1))
            fallback_color = normalize_color(fallback) if fallback is not None else generated_fallback
            mapping = {
                str(category): palette.colors[idx % len(palette.colors)]
                for idx, category in enumerate(categories)
            }
            return CategoricalColorScheme(
                name=scheme,
                mapping=mapping,
                fallback=fallback_color,
                source=palette.source,
            )
        if isinstance(scheme, Mapping):
            mapping = {str(key): normalize_color(value) for key, value in scheme.items()}
            fallback_color = None if fallback is None else normalize_color(fallback)
            return CategoricalColorScheme(name=None, mapping=mapping, fallback=fallback_color)
        if categories is not None:
            palette = self.resolve_palette(scheme, samples=max(len(categories), 1))
            mapping = {
                str(category): palette.colors[idx % len(palette.colors)]
                for idx, category in enumerate(categories)
            }
            fallback_color = None if fallback is None else normalize_color(fallback)
            return CategoricalColorScheme(name=None, mapping=mapping, fallback=fallback_color, source=palette.source)
        raise ValueError("Categorical schemes require either a mapping or explicit categories.")

    def register_scheme(
        self,
        name: str,
        scheme: Any,
        *,
        categories: Sequence[Any] | None = None,
        fallback: Any | None = None,
        overwrite: bool = False,
    ) -> CategoricalColorScheme:
        key = str(name).strip()
        if key == "":
            raise ValueError("Color scheme name must be a non-empty string.")
        if key in self._schemes and not overwrite:
            raise ValueError(f"Color scheme {key!r} already exists.")
        resolved = self.resolve_scheme(scheme, categories=categories, fallback=fallback)
        stored = CategoricalColorScheme(
            name=key,
            mapping=dict(resolved.mapping),
            fallback=resolved.fallback,
            source=resolved.source,
        )
        self._schemes[key] = stored
        return stored

    def register_generated_scheme(
        self,
        name: str,
        palette: Any,
        *,
        fallback: Any | None = None,
        overwrite: bool = False,
    ) -> str:
        key = str(name).strip()
        if key == "":
            raise ValueError("Color scheme name must be a non-empty string.")
        if (key in self._schemes or key in self._generated_scheme_palettes) and not overwrite:
            raise ValueError(f"Color scheme {key!r} already exists.")
        fallback_color = None if fallback is None else normalize_color(fallback)
        self._generated_scheme_palettes[key] = (palette, fallback_color)
        return key

    def _palette_from_name_or_matplotlib(self, palette: str, *, samples: int) -> ContinuousPalette:
        token = palette.strip()
        mpl_name = token[4:] if token.lower().startswith("mpl:") else token
        try:
            import matplotlib
        except Exception as exc:
            raise ValueError(f"Unknown palette {palette!r} and matplotlib is not available.") from exc
        try:
            cmap = matplotlib.colormaps[mpl_name]
        except Exception as exc:
            raise ValueError(f"Unknown palette {palette!r}.") from exc
        return self._palette_from_matplotlib_or_sequence(cmap, samples=samples, name=token, source="matplotlib")

    def _palette_from_matplotlib_or_sequence(
        self,
        palette: Any,
        *,
        samples: int,
        name: str | None = None,
        source: str = "custom",
    ) -> ContinuousPalette:
        if isinstance(palette, (list, tuple)):
            colors = normalize_colors(palette)
            if len(colors) == 0:
                raise ValueError("Palettes must contain at least one color.")
            return ContinuousPalette(name=name, colors=colors, source=source)

        try:
            import matplotlib.colors as mcolors
        except Exception:
            mcolors = None

        if mcolors is not None and isinstance(palette, mcolors.Colormap):
            steps = max(int(samples), 2)
            colors = [
                _rgb_to_int(tuple(float(channel) for channel in palette(idx / (steps - 1))[:3]))
                for idx in range(steps)
            ]
            return ContinuousPalette(name=name or getattr(palette, "name", None), colors=colors, source="matplotlib")

        raise ValueError(f"Unsupported palette value {palette!r}.")


colors = ColorRegistry()

def _register_builtin_palettes() -> None:
    for name in ("turbo", "viridis", "plasma", "magma", "inferno", "rainbow"):
        try:
            colors.register_palette(name, f"mpl:{name}", overwrite=True)
        except Exception:
            # Keep import-time behavior soft when matplotlib is not available.
            continue


_register_builtin_palettes()

colors.register_palette(
    "categorical_default",
    ["blue", "orange", "green", "red", "purple", "gray", "pink", "brown"],
    overwrite=True,
)

colors.register_scheme(
    "pharmacophore_default",
    {
        "donor": 0x3B82F6,
        "acceptor": 0xEF4444,
        "hydrophobe": 0xF59E0B,
        "aromatic": 0x8B5CF6,
        "positive": 0x2563EB,
        "negative": 0xF43F5E,
        "metal": 0x10B981,
    },
    overwrite=True,
)

colors.register_scheme(
    "element_cpk",
    {
        "H": "white",
        "C": "grey",
        "N": "blue",
        "O": "red",
        "S": "yellow",
        "P": "orange",
        "F": "green",
        "CL": "green",
        "BR": "darkred",
        "I": "purple",
        "FE": "darkorange",
        "ZN": "slategray",
        "MG": "forestgreen",
        "CA": "darkgreen",
        "NA": "blue",
        "K": "violet",
    },
    fallback="lightgrey",
    overwrite=True,
)

colors.register_scheme(
    "secondary_structure_default",
    {
        "H": "red",
        "G": "deeppink",
        "I": "mediumvioletred",
        "E": "dodgerblue",
        "B": "cornflowerblue",
        "T": "turquoise",
        "S": "lightgreen",
        "L": "lightgrey",
        "C": "lightgrey",
        "helix": "red",
        "sheet": "dodgerblue",
        "turn": "turquoise",
        "coil": "lightgrey",
    },
    fallback="lightgrey",
    overwrite=True,
)

colors.register_generated_scheme(
    "chain_default",
    "categorical_default",
    fallback="lightgrey",
    overwrite=True,
)

colors.register_generated_scheme(
    "pocket_default",
    "categorical_default",
    fallback="lightgrey",
    overwrite=True,
)


def expand_values_to_atoms(
    molsys: "Any",
    values: "Any",
    element: str = "atom",
    palette: "Any" = "viridis",
    value_range: "tuple[float, float] | list[float] | None" = None,
    scope_atom_indices: "list[int] | None" = None,
) -> "tuple[list[int], list[int]]":
    """Map element-level scalar values to a flat (atom_indices, colors) pair.

    For each element in *molsys* (optionally scoped to *scope_atom_indices*),
    the corresponding scalar is converted to a color and broadcast to every
    atom that belongs to that element.

    Parameters
    ----------
    molsys
        A MolSysMT molecular system.
    values
        Iterable of scalars, one per element at the requested *element* level
        that exists in *molsys* (or in the scope if *scope_atom_indices* is
        given).
    element
        Structural hierarchy level: ``"atom"``, ``"group"``, ``"component"``,
        ``"molecule"``, ``"chain"``, ``"entity"``.  Defaults to ``"atom"``.
    palette
        Palette name, matplotlib colormap, or list of colors.
    value_range
        Normalization range ``[vmin, vmax]``.  Auto-computed when ``None``.
    scope_atom_indices
        If given, only atoms in this list are considered and only elements that
        have at least one atom here are included.

    Returns
    -------
    atom_indices : list[int]
        Flat list of model-level atom indices.
    colors : list[int]
        Parallel list of 0xRRGGBB color integers.
    """
    import molsysmt as msm  # lazy import

    color_list = scalar_to_color_list(values, palette=palette, value_range=value_range)

    if element == "atom":
        if scope_atom_indices is not None:
            if len(color_list) != len(scope_atom_indices):
                raise ValueError(
                    f"values length ({len(color_list)}) does not match "
                    f"atom count in scope ({len(scope_atom_indices)})."
                )
            return list(scope_atom_indices), color_list

        n_atoms = int(msm.get(molsys, element="system", n_atoms=True, skip_digestion=True))
        if len(color_list) != n_atoms:
            raise ValueError(
                f"values length ({len(color_list)}) does not match atom count ({n_atoms})."
            )
        return list(range(n_atoms)), color_list

    # Non-atom level: map element index → atom indices via msm.get
    _ELEM_TO_ATOM_ATTR: dict[str, str] = {
        "group": "group_index",
        "component": "component_index",
        "molecule": "molecule_index",
        "chain": "chain_index",
        "entity": "entity_index",
    }
    if element not in _ELEM_TO_ATOM_ATTR:
        raise ValueError(
            f"Unsupported element level {element!r}. "
            f"Accepted: 'atom', 'group', 'component', 'molecule', 'chain', 'entity'."
        )

    attr = _ELEM_TO_ATOM_ATTR[element]

    # Get the element-level index for every atom (shape: (n_atoms,))
    per_atom_elem_index = msm.get(
        molsys,
        element="atom",
        selection="all" if scope_atom_indices is None else list(scope_atom_indices),
        output_type="values",
        skip_digestion=True,
        **{attr: True},
    )

    # Build sorted unique element indices
    unique_elem_indices = sorted(set(int(v) for v in per_atom_elem_index if v is not None))

    if len(color_list) != len(unique_elem_indices):
        raise ValueError(
            f"values length ({len(color_list)}) does not match "
            f"{element} count ({len(unique_elem_indices)}) "
            f"{'in scope ' if scope_atom_indices is not None else ''}in the system."
        )

    elem_to_color = {eidx: color_list[pos] for pos, eidx in enumerate(unique_elem_indices)}

    # Determine the atom indices to color
    if scope_atom_indices is not None:
        atom_list = list(scope_atom_indices)
    else:
        n_atoms = int(msm.get(molsys, element="system", n_atoms=True, skip_digestion=True))
        atom_list = list(range(n_atoms))

    out_atom_indices: list[int] = []
    out_colors: list[int] = []
    default_color = 0xAAAAAA
    for i, atom_idx in enumerate(atom_list):
        eidx_val = per_atom_elem_index[i]
        if eidx_val is None:
            continue
        color = elem_to_color.get(int(eidx_val), default_color)
        out_atom_indices.append(atom_idx)
        out_colors.append(color)

    return out_atom_indices, out_colors


def scalar_to_color_list(
    values: Any,
    palette: Any = "viridis",
    value_range: "tuple[float, float] | list[float] | None" = None,
) -> list[int]:
    """Map an iterable of scalar values to a list of 0xRRGGBB color integers.

    Parameters
    ----------
    values
        Iterable of numeric values.  One color is returned per value.
    palette
        Palette name (str), ``ContinuousPalette``, matplotlib ``Colormap``, or a
        list of colors.  Defaults to ``"viridis"``.
    value_range
        ``(vmin, vmax)`` normalization range.  Auto-calculated from *values* when
        ``None``.

    Returns
    -------
    list[int]
        One 0xRRGGBB integer per input value.
    """
    import numpy as np  # lazy import — only needed when called

    arr = np.asarray(list(values), dtype=float)
    if arr.ndim != 1:
        raise ValueError("values must be a 1-D sequence of scalars.")

    if value_range is not None:
        vmin, vmax = float(value_range[0]), float(value_range[1])
    else:
        vmin, vmax = float(arr.min()), float(arr.max())

    span = vmax - vmin
    normed = np.zeros_like(arr) if span == 0 else np.clip((arr - vmin) / span, 0.0, 1.0)

    palette_obj = colors.resolve_palette(palette, samples=256)
    palette_ints = palette_obj.colors  # list[int], 0xRRGGBB
    n = len(palette_ints) - 1

    return [palette_ints[int(round(float(v) * n))] for v in normed]


__all__ = [
    "MOLSTAR_COLOR_NAMES",
    "ContinuousPalette",
    "CategoricalColorScheme",
    "ColorRegistry",
    "colors",
    "normalize_color",
    "normalize_colors",
    "scalar_to_color_list",
]
