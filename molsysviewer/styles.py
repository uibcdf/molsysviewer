from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from smonitor import signal

from ._private.arg_digestion import digest
from .config.user_presets import user_presets
from .viewer.presets import ALLOWED_PRESETS, PRESET_ALIASES
from .viewer.representations import (
    ALLOWED_REPRESENTATIONS,
    COMMON_REPRESENTATION_PARAMS,
    REPRESENTATION_ALIASES,
    REPRESENTATION_PARAM_SCHEMAS,
    normalize_representation_type,
)


@dataclass(frozen=True)
class Style:
    """First-slice semantic wrapper over the current scene representation contract."""

    representation: str | None = None
    preset: str | None = None
    user_preset: str | None = None
    name: str | None = None
    kind: str = "scene"
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.params, dict):
            raise ValueError("Style params must be provided as a dictionary.")
        if self.kind == "focus":
            if self.preset is not None or self.user_preset is not None:
                raise ValueError("Focus styles only support representation (not preset or user_preset).")
            if self.representation is None:
                raise ValueError("Focus styles require a representation.")
            return
        if self.kind != "scene":
            raise ValueError("Style kind must be 'scene' or 'focus'.")
        defined = sum(
            value is not None
            for value in (self.representation, self.preset, self.user_preset)
        )
        if defined != 1:
            raise ValueError("Style requires exactly one of representation, preset, or user_preset.")

    def info(self) -> dict[str, Any]:
        """Return a JSON-friendly summary of the style object."""
        return {
            "kind": self.kind,
            "name": self.name,
            "representation": self.representation,
            "preset": self.preset,
            "user_preset": self.user_preset,
            "params": dict(self.params),
        }


BUILTIN_SCENE_STYLES: dict[str, Style] = {
    "default": Style(preset="auto", name="Default"),
    "polymer-cartoon": Style(preset="polymer-cartoon", name="Polymer Cartoon"),
    "polymer-and-ligand": Style(preset="polymer-and-ligand", name="Polymer And Ligand"),
    "atomic-detail": Style(preset="atomic-detail", name="Atomic Detail"),
    "coarse-surface": Style(preset="coarse-surface", name="Coarse Surface"),
    "cartoon-secondary-structure": Style(
        representation="cartoon",
        name="Cartoon Secondary Structure",
        params={"color_scheme": "secondary_structure_default"},
    ),
    "cartoon-chain": Style(
        representation="cartoon",
        name="Cartoon Chain",
        params={"color_scheme": "chain_default"},
    ),
    "ball-and-stick-element-cpk": Style(
        representation="ball-and-stick",
        name="Ball And Stick Element CPK",
        params={"color_scheme": "element_cpk"},
    ),
    "spacefill-element-cpk": Style(
        representation="spacefill",
        name="Spacefill Element CPK",
        params={"color_scheme": "element_cpk"},
    ),
    "empty": Style(preset="empty", name="Empty"),
}


BUILTIN_FOCUS_STYLES: dict[str, Style] = {
    "hydrophobicity": Style(
        representation="molecular-surface",
        name="Hydrophobicity Surface",
        kind="focus",
        params={"molstar_color_theme": {"name": "hydrophobicity", "params": {}}},
    ),
    "secondary-structure": Style(
        representation="cartoon",
        name="Secondary Structure",
        kind="focus",
        params={"color_scheme": "secondary_structure_default"},
    ),
    "chain-id": Style(
        representation="cartoon",
        name="Chain ID",
        kind="focus",
        params={"color_scheme": "chain_default"},
    ),
    "element-cpk": Style(
        representation="ball-and-stick",
        name="Element CPK",
        kind="focus",
        params={"color_scheme": "element_cpk"},
    ),
}


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
    "residue_name": {
        "molstar_theme": "residue-name",
        "description": "Color by residue or group name.",
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


STRUCTURAL_SIZE_SCHEMES: dict[str, dict[str, Any]] = {
    "uniform": {
        "molstar_theme": "uniform",
        "description": "Use a uniform structural size theme.",
    },
    "physical": {
        "molstar_theme": "physical",
        "description": "Use physical radii where supported by the representation.",
    },
    "uncertainty": {
        "molstar_theme": "uncertainty",
        "description": "Scale by uncertainty-related values where available.",
    },
}


ADVANCED_MOLSTAR_COLOR_THEMES: dict[str, dict[str, Any]] = {
    "uniform": {"category": "misc"},
    "occupancy": {"category": "misc"},
    "hydrophobicity": {"category": "residue"},
    "element-index": {"category": "atom"},
    "element-symbol": {"category": "atom"},
    "shape-group": {"category": "misc"},
    "uncertainty": {"category": "validation"},
    "volume-value": {"category": "misc"},
    "carbohydrate-symbol": {"category": "residue"},
    "chain-id": {"category": "chain"},
    "operator-name": {"category": "symmetry"},
    "entity-id": {"category": "chain"},
    "entity-source": {"category": "chain"},
    "model-index": {"category": "misc"},
    "structure-index": {"category": "misc"},
    "unit-index": {"category": "misc"},
    "trajectory-index": {"category": "misc"},
    "molecule-type": {"category": "residue"},
    "polymer-id": {"category": "chain"},
    "polymer-index": {"category": "chain"},
    "residue-name": {"category": "residue"},
    "secondary-structure": {"category": "residue"},
    "sequence-id": {"category": "residue"},
    "illustrative": {"category": "misc"},
    "operator-hkl": {"category": "symmetry"},
    "partial-charge": {"category": "validation"},
    "atom-id": {"category": "atom"},
    "volume-segment": {"category": "misc"},
    "external-volume": {"category": "misc"},
    "cartoon": {"category": "misc"},
    "formal-charge": {"category": "validation"},
    "external-structure": {"category": "misc"},
    "volume-instance": {"category": "misc"},
}


ADVANCED_MOLSTAR_SIZE_THEMES: dict[str, dict[str, Any]] = {
    "uniform": {"category": "misc"},
    "physical": {"category": "atom"},
    "uncertainty": {"category": "validation"},
    "shape-group": {"category": "misc"},
    "volume-value": {"category": "misc"},
}


class StylesManager:
    """Scene-style manager backed by the existing whole-representation API."""

    def __init__(self, view: Any) -> None:
        self._view = view
        self._last_applied_name: str | None = None
        self._registry: dict[str, dict[str, Any]] = {}
        self._focus_registry: dict[str, dict[str, Any]] = {}
        self._focus_counter: int = 0

    def _resolve_named_style(self, tag: str) -> Style | None:
        record = self._registry.get(tag)
        if record is not None:
            return record["style"]
        return BUILTIN_SCENE_STYLES.get(tag)

    def _clear_cached_name(self) -> None:
        self._last_applied_name = None

    def _current_style(self) -> Style | None:
        whole = self._view.whole
        representation = getattr(whole, "_representation", None)
        preset = getattr(whole, "_preset", None)
        params = dict(getattr(whole, "_repr_params", {}) or {})

        if representation is None and preset is None:
            return None

        if preset is not None and preset in user_presets:
            return Style(
                user_preset=preset,
                name=self._last_applied_name,
                params=params,
            )

        if preset is not None:
            return Style(
                preset=preset,
                name=self._last_applied_name,
                params=params,
            )

        return Style(
            representation=representation,
            name=self._last_applied_name,
            params=params,
        )

    @signal(tags=["style"])
    @digest()
    def apply(
        self,
        style: Style | None = None,
        *,
        tag: str | None = None,
        representation: str | None = None,
        preset: str | None = None,
        skip_digestion: bool = False,
        **params: Any,
    ) -> Style:
        """Apply the first-slice scene style by delegating to ``view.whole.set_representation()``."""
        if tag is not None:
            if style is not None or representation is not None or preset is not None or params:
                raise ValueError("styles.apply(tag=...) does not accept style, representation, preset, or params.")
            style = self._resolve_named_style(tag)
            if style is None:
                raise ValueError(f"No style found for tag {tag!r}.")

        if style is not None and (representation is not None or preset is not None or params):
            raise ValueError("styles.apply(style=...) does not accept additional representation, preset, or params.")

        resolved = style
        if resolved is None:
            resolved = Style(representation=representation, preset=preset, params=dict(params))

        target_preset = resolved.user_preset if resolved.user_preset is not None else resolved.preset
        self._view.whole.set_representation(  # noqa: SLF001
            resolved.representation,
            preset=target_preset,
            skip_digestion=True,
            **resolved.params,
        )
        self._last_applied_name = resolved.name
        return resolved

    @signal(tags=["style"])
    @digest()
    def add(
        self,
        tag: str,
        style: Style,
        *,
        description: str | None = None,
        source: str = "runtime",
        skip_digestion: bool = False,
    ) -> Style:
        """Register a reusable named style in the Python-side style registry."""
        self._registry[tag] = {
            "tag": tag,
            "style": style,
            "description": description,
            "source": source,
        }
        return style

    @signal(tags=["style"])
    @digest()
    def contains(self, tag: str, skip_digestion: bool = False) -> bool:
        """Return whether a named style exists in the registry."""
        return tag in self._registry

    @signal(tags=["style"])
    @digest()
    def get(self, tag: str, skip_digestion: bool = False) -> Style | None:
        """Return the registered style for a tag, if present."""
        record = self._registry.get(tag)
        if record is None:
            return None
        return record["style"]

    @signal(tags=["style"])
    @digest()
    def tags(self, skip_digestion: bool = False) -> list[str]:
        """Return registered style tags."""
        return sorted(self._registry.keys())

    @signal(tags=["style"])
    @digest()
    def count(self, skip_digestion: bool = False) -> int:
        """Return the number of registered styles."""
        return len(self._registry)

    @signal(tags=["style"])
    @digest()
    def records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return JSON-friendly records for the registered styles."""
        records: list[dict[str, Any]] = []
        for tag in self.tags(skip_digestion=True):
            record = self._registry[tag]
            style = record["style"]
            records.append(
                {
                    "tag": tag,
                    "description": record.get("description"),
                    "source": record.get("source"),
                    "style": style.info(),
                }
            )
        return records

    @signal(tags=["style"])
    @digest()
    def clear(self, tag: str | None = None, skip_digestion: bool = False) -> None:
        """Clear one registered style or the whole style registry."""
        if tag is None:
            self._registry.clear()
            return
        self._registry.pop(tag, None)

    @signal(tags=["style", "query"])
    @digest()
    def builtin_tags(self, skip_digestion: bool = False) -> list[str]:
        """Return the canonical built-in scene-style tags."""
        return sorted(BUILTIN_SCENE_STYLES.keys())

    @signal(tags=["style", "query"])
    @digest()
    def representation_types(self, skip_digestion: bool = False) -> list[str]:
        """Return canonical public structural representation names."""
        return sorted(ALLOWED_REPRESENTATIONS)

    @signal(tags=["style", "query"])
    @digest()
    def representation_type_records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return public representation names and aliases."""
        reverse_aliases: dict[str, list[str]] = {name: [] for name in ALLOWED_REPRESENTATIONS}
        for alias, canonical in REPRESENTATION_ALIASES.items():
            reverse_aliases.setdefault(canonical, []).append(alias)
        return [
            {
                "tag": tag,
                "aliases": sorted(reverse_aliases.get(tag, [])),
            }
            for tag in self.representation_types(skip_digestion=True)
        ]

    @signal(tags=["style", "query"])
    @digest()
    def representation_presets(self, skip_digestion: bool = False) -> list[str]:
        """Return canonical public structural preset names."""
        return sorted(ALLOWED_PRESETS)

    @signal(tags=["style", "query"])
    @digest()
    def representation_preset_records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return public preset names and aliases."""
        reverse_aliases: dict[str, list[str]] = {name: [] for name in ALLOWED_PRESETS}
        for alias, canonical in PRESET_ALIASES.items():
            reverse_aliases.setdefault(canonical, []).append(alias)
        return [
            {
                "tag": tag,
                "aliases": sorted(reverse_aliases.get(tag, [])),
            }
            for tag in self.representation_presets(skip_digestion=True)
        ]

    @signal(tags=["style", "query"])
    @digest()
    def representation_param_schema(self, representation: str, skip_digestion: bool = False) -> dict[str, Any]:
        """Return the curated public parameter schema for one representation."""
        tag = normalize_representation_type(representation)
        if tag is None:
            raise ValueError("Representation name is required.")
        schema = REPRESENTATION_PARAM_SCHEMAS[tag]
        return {
            "tag": tag,
            "summary": schema["summary"],
            "common_params": [dict(item) for item in COMMON_REPRESENTATION_PARAMS],
            "specific_params": [dict(item) for item in schema["specific_params"]],
        }

    @signal(tags=["style", "query"])
    @digest()
    def representation_param_schema_records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return the curated public parameter schemas for all representations."""
        return [
            self.representation_param_schema(tag, skip_digestion=True)
            for tag in self.representation_types(skip_digestion=True)
        ]

    @signal(tags=["style", "query"])
    @digest()
    def structural_color_schemes(self, skip_digestion: bool = False) -> list[str]:
        """Return curated public structural color-scheme names."""
        return sorted(STRUCTURAL_COLOR_SCHEMES.keys())

    @signal(tags=["style", "query"])
    @digest()
    def structural_color_scheme_records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return public structural color-scheme metadata."""
        return [
            {
                "tag": tag,
                **STRUCTURAL_COLOR_SCHEMES[tag],
            }
            for tag in self.structural_color_schemes(skip_digestion=True)
        ]

    @signal(tags=["style", "query"])
    @digest()
    def structural_size_schemes(self, skip_digestion: bool = False) -> list[str]:
        """Return curated public structural size-scheme names."""
        return sorted(STRUCTURAL_SIZE_SCHEMES.keys())

    @signal(tags=["style", "query"])
    @digest()
    def structural_size_scheme_records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return public structural size-scheme metadata."""
        return [
            {
                "tag": tag,
                **STRUCTURAL_SIZE_SCHEMES[tag],
            }
            for tag in self.structural_size_schemes(skip_digestion=True)
        ]

    @signal(tags=["style", "query"])
    @digest()
    def molstar_color_themes(self, skip_digestion: bool = False) -> list[str]:
        """Return advanced Mol* structural color-theme names."""
        return sorted(ADVANCED_MOLSTAR_COLOR_THEMES.keys())

    @signal(tags=["style", "query"])
    @digest()
    def molstar_color_theme_records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return advanced Mol* structural color-theme metadata."""
        return [
            {
                "tag": tag,
                **ADVANCED_MOLSTAR_COLOR_THEMES[tag],
            }
            for tag in self.molstar_color_themes(skip_digestion=True)
        ]

    @signal(tags=["style", "query"])
    @digest()
    def molstar_size_themes(self, skip_digestion: bool = False) -> list[str]:
        """Return advanced Mol* structural size-theme names."""
        return sorted(ADVANCED_MOLSTAR_SIZE_THEMES.keys())

    @signal(tags=["style", "query"])
    @digest()
    def molstar_size_theme_records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return advanced Mol* structural size-theme metadata."""
        return [
            {
                "tag": tag,
                **ADVANCED_MOLSTAR_SIZE_THEMES[tag],
            }
            for tag in self.molstar_size_themes(skip_digestion=True)
        ]

    @signal(tags=["style", "query"])
    @digest()
    def get_builtin(self, tag: str, skip_digestion: bool = False) -> Style | None:
        """Return one canonical built-in scene style, if present."""
        return BUILTIN_SCENE_STYLES.get(tag)

    @signal(tags=["style", "query"])
    @digest()
    def builtin_records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return JSON-friendly records for the canonical built-in scene styles."""
        records: list[dict[str, Any]] = []
        for tag in self.builtin_tags(skip_digestion=True):
            style = BUILTIN_SCENE_STYLES[tag]
            records.append(
                {
                    "tag": tag,
                    "description": None,
                    "source": "builtin",
                    "style": style.info(),
                }
            )
        return records

    @signal(tags=["style", "config"])
    @digest()
    def load_project_config(
        self,
        path: str,
        *,
        apply_default: bool = False,
        skip_digestion: bool = False,
    ) -> dict[str, Any]:
        """Load styles from an explicit ``_molsysviewer.py``-style project config file."""
        from .config.project_config import load_project_config

        config = load_project_config(path, skip_digestion=True)
        default_scene_style = config.get("default_scene_style")
        for tag, style in (config.get("styles") or {}).items():
            self.add(tag, style, source="project-config", skip_digestion=True)
        if apply_default and isinstance(default_scene_style, Style):
            self.apply(style=default_scene_style, skip_digestion=True)
        return {
            "path": config.get("path"),
            "default_scene_style": None if default_scene_style is None else default_scene_style.info(),
            "style_tags": sorted((config.get("styles") or {}).keys()),
            "applied_default": bool(apply_default and isinstance(default_scene_style, Style)),
        }

    @signal(tags=["style", "query"])
    @digest()
    def current(self, skip_digestion: bool = False) -> Style | None:
        """Return the currently active first-slice scene style, if any."""
        return self._current_style()

    @signal(tags=["style", "query"])
    @digest()
    def info(self, skip_digestion: bool = False) -> dict[str, Any] | None:
        """Return a JSON-friendly summary of the currently active first-slice scene style."""
        current = self._current_style()
        if current is None:
            return None
        return current.info()

    def _next_focus_tag(self) -> str:
        self._focus_counter += 1
        return f"focus{self._focus_counter}"

    @signal(tags=["style", "focus"])
    @digest()
    def focus(
        self,
        style_or_tag: "Style | str | None" = None,
        *,
        tag: str | None = None,
        selection: "str | Any" = "all",
        atom_indices: "list[int] | None" = None,
        representation: "str | None" = None,
        skip_digestion: bool = False,
        **params: Any,
    ) -> str:
        """Apply a focus style as a cumulative overlay on a selection.

        Parameters
        ----------
        style_or_tag
            A ``Style`` object with ``kind='focus'``, or a builtin focus-style tag string.
        tag
            Tag to assign to both the focus entry and the region. Auto-generated if omitted.
        selection
            MolSysMT selection string. Defaults to ``"all"``.
        atom_indices
            Explicit atom indices (bypasses selection).
        representation
            Inline representation (alternative to providing a full ``Style``).
        **params
            Additional representation parameters forwarded when using inline ``representation``.
        """
        if isinstance(style_or_tag, str):
            builtin = BUILTIN_FOCUS_STYLES.get(style_or_tag)
            if builtin is None:
                raise ValueError(f"No builtin focus style found for {style_or_tag!r}.")
            resolved = builtin
            resolved_tag = tag or style_or_tag
        elif isinstance(style_or_tag, Style):
            if style_or_tag.kind != "focus":
                raise ValueError("styles.focus() requires a Style with kind='focus'.")
            resolved = style_or_tag
            resolved_tag = tag or self._next_focus_tag()
        elif style_or_tag is None and representation is not None:
            resolved = Style(representation=representation, kind="focus", params=dict(params))
            resolved_tag = tag or self._next_focus_tag()
        else:
            raise ValueError(
                "styles.focus() requires a style object, a builtin tag string, or representation=."
            )

        region = self._view.new_region(
            selection=selection,
            atom_indices=atom_indices,
            tag=resolved_tag,
            representation=resolved.representation,
            skip_digestion=True,
            **resolved.params,
        )
        self._focus_registry[resolved_tag] = {"style": resolved, "region_tag": region.tag}
        return resolved_tag

    @signal(tags=["style", "focus"])
    @digest()
    def clear_focus(self, tag: "str | None" = None, skip_digestion: bool = False) -> None:
        """Remove one focus overlay or all active focus overlays."""
        if tag is not None:
            entry = self._focus_registry.pop(tag, None)
            if entry is None:
                return
            region = self._view.regions.get(entry["region_tag"])
            if region is not None:
                region.delete(skip_digestion=True)
        else:
            for entry in list(self._focus_registry.values()):
                region = self._view.regions.get(entry["region_tag"])
                if region is not None:
                    region.delete(skip_digestion=True)
            self._focus_registry.clear()

    @signal(tags=["style", "query"])
    @digest()
    def focus_tags(self, skip_digestion: bool = False) -> list[str]:
        """Return active focus overlay tags."""
        return sorted(self._focus_registry.keys())

    @signal(tags=["style", "query"])
    @digest()
    def builtin_focus_tags(self, skip_digestion: bool = False) -> list[str]:
        """Return canonical built-in focus-style tags."""
        return sorted(BUILTIN_FOCUS_STYLES.keys())

    @signal(tags=["style", "query"])
    @digest()
    def get_builtin_focus(self, tag: str, skip_digestion: bool = False) -> "Style | None":
        """Return one canonical built-in focus style, if present."""
        return BUILTIN_FOCUS_STYLES.get(tag)

    @signal(tags=["style", "query"])
    @digest()
    def builtin_focus_records(self, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return JSON-friendly records for the canonical built-in focus styles."""
        records: list[dict[str, Any]] = []
        for ftag in self.builtin_focus_tags(skip_digestion=True):
            style = BUILTIN_FOCUS_STYLES[ftag]
            records.append({
                "tag": ftag,
                "description": None,
                "source": "builtin",
                "style": style.info(),
            })
        return records

__all__ = [
    "Style",
    "StylesManager",
    "BUILTIN_SCENE_STYLES",
    "BUILTIN_FOCUS_STYLES",
    "STRUCTURAL_COLOR_SCHEMES",
    "STRUCTURAL_SIZE_SCHEMES",
    "ADVANCED_MOLSTAR_COLOR_THEMES",
    "ADVANCED_MOLSTAR_SIZE_THEMES",
]
