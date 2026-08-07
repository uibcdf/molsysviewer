from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

from .._private.argdigest import digest


@digest()
def load_project_config(path: str | Path, skip_digestion: bool = False) -> dict[str, Any]:
    """Load an explicit ``_molsysviewer.py``-style project config file.

    Supported top-level names:

    - ``DEFAULT_SCENE_STYLE``: optional :class:`Style`
    - ``STYLES``: optional mapping ``tag -> Style``
    - ``ADDONS_ENABLED``: optional iterable of add-on names enabled by default
    - ``ADDONS_DISABLED``: optional iterable of add-on names disabled by default
    """
    from ..styles import Style

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Project config file not found: {file_path}")

    spec = spec_from_file_location("molsysviewer_project_config", file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load project config module from {file_path}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    default_scene_style = getattr(module, "DEFAULT_SCENE_STYLE", None)
    if default_scene_style is not None and not isinstance(default_scene_style, Style):
        raise ValueError("DEFAULT_SCENE_STYLE must be a molsysviewer.styles.Style instance.")

    styles = getattr(module, "STYLES", {})
    if styles is None:
        styles = {}
    if not isinstance(styles, dict):
        raise ValueError("STYLES must be a mapping of tag -> Style.")

    validated_styles: dict[str, Style] = {}
    for tag, style in styles.items():
        if not isinstance(tag, str):
            raise ValueError("STYLES keys must be strings.")
        if not isinstance(style, Style):
            raise ValueError(f"STYLES[{tag!r}] must be a molsysviewer.styles.Style instance.")
        validated_styles[tag] = style

    def _normalize_addon_names(value: Any, field_name: str) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str) or not isinstance(value, (list, tuple, set)):
            raise ValueError(f"{field_name} must be an iterable of add-on names.")
        names: list[str] = []
        for item in value:
            if not isinstance(item, str) or item.strip() == "":
                raise ValueError(f"{field_name} items must be non-empty strings.")
            names.append(item.strip())
        return sorted(set(names))

    addons_enabled = _normalize_addon_names(getattr(module, "ADDONS_ENABLED", []), "ADDONS_ENABLED")
    addons_disabled = _normalize_addon_names(getattr(module, "ADDONS_DISABLED", []), "ADDONS_DISABLED")
    overlap = sorted(set(addons_enabled).intersection(addons_disabled))
    if overlap:
        raise ValueError(f"ADDONS_ENABLED and ADDONS_DISABLED must not overlap: {', '.join(overlap)}")

    return {
        "path": str(file_path),
        "default_scene_style": default_scene_style,
        "styles": validated_styles,
        "addons_enabled": addons_enabled,
        "addons_disabled": addons_disabled,
    }


__all__ = ["load_project_config"]
