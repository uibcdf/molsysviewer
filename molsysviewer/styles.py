from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from smonitor import signal

from ._private.arg_digestion import digest
from .config.user_presets import user_presets


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
        defined = sum(
            value is not None
            for value in (self.representation, self.preset, self.user_preset)
        )
        if self.kind != "scene":
            raise ValueError("The first Style slice only supports kind='scene'.")
        if defined != 1:
            raise ValueError("Style requires exactly one of representation, preset, or user_preset.")
        if not isinstance(self.params, dict):
            raise ValueError("Style params must be provided as a dictionary.")

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
    "empty": Style(preset="empty", name="Empty"),
}


class StylesManager:
    """Scene-style manager backed by the existing whole-representation API."""

    def __init__(self, view: Any) -> None:
        self._view = view
        self._last_applied_name: str | None = None
        self._registry: dict[str, dict[str, Any]] = {}

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

__all__ = ["Style", "StylesManager", "BUILTIN_SCENE_STYLES"]
