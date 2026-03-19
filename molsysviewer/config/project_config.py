from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

from .._private.arg_digestion import digest


@digest()
def load_project_config(path: str | Path, skip_digestion: bool = False) -> dict[str, Any]:
    """Load an explicit ``_molsysviewer.py``-style project config file.

    Supported top-level names:

    - ``DEFAULT_SCENE_STYLE``: optional :class:`Style`
    - ``STYLES``: optional mapping ``tag -> Style``
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

    return {
        "path": str(file_path),
        "default_scene_style": default_scene_style,
        "styles": validated_styles,
    }


__all__ = ["load_project_config"]
