from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Dict

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

# Registry of user-defined presets. Shape:
# {
#   "name": {
#       "base": "auto",
#       "options": {...},
#       "rules": [
#           {"selection": "...", "representation": "...", "params": {...}},
#           {"atom_indices": [0,1,2], "representation": "..."},
#       ],
#   },
# }
user_presets: Dict[str, Dict[str, Any]] = {}


def load_user_presets(path: str | Path) -> Dict[str, Dict[str, Any]]:
    """Load user presets from a JSON or YAML file into ``user_presets``.

    The file must contain a top-level mapping: preset_name -> {base, options, rules}.
    YAML support requires ``pyyaml``; falls back to JSON otherwise.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Preset file not found: {file_path}")

    text = file_path.read_text()
    data: Dict[str, Any]
    if file_path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise ImportError("pyyaml is required to load YAML presets; install pyyaml or use JSON.")
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError("Preset file must define a top-level mapping (dict).")

    # Shallow validation: ensure each entry is a mapping
    for name, cfg in data.items():
        if not isinstance(cfg, dict):
            raise ValueError(f"Preset '{name}' must be a mapping (found {type(cfg)})")
    user_presets.update(data)
    return user_presets


__all__ = ["user_presets", "load_user_presets"]
