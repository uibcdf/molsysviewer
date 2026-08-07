from __future__ import annotations

from typing import Any

import molsysmt as msm

from ..config.user_presets import user_presets

PRESET_ALIASES = {
    "automatic": "auto",
}

ALLOWED_PRESETS = {
    "auto",
    "atomic-detail",
    "polymer-and-ligand",
    "polymer-cartoon",
    "coarse-surface",
    "empty",
}


def normalize_representation_preset(value: str | None) -> str | None:
    if value is None:
        return None
    key = value.replace("_", "-").lower().strip()
    key = PRESET_ALIASES.get(key, key)
    if key in ALLOWED_PRESETS:
        return key
    if key in user_presets:
        return key
    raise ValueError(
        f"Unsupported preset '{value}'. Allowed: {sorted(ALLOWED_PRESETS)} + user presets {list(user_presets)}"
    )


def resolve_user_preset(view: Any, preset: str | None) -> dict[str, Any] | None:
    if preset is None:
        return None
    key = preset.replace("_", "-").lower().strip()
    cfg = user_presets.get(key)
    if cfg is None:
        return None
    if getattr(view, "_molsys", None) is None:
        raise ValueError("User presets require a loaded molecular system to resolve selections.")

    rules = []
    for rule in cfg.get("rules", []) or []:
        if not isinstance(rule, dict):
            continue
        new_rule = dict(rule)
        if "atom_indices" not in new_rule:
            sel = new_rule.get("selection")
            if sel is not None:
                try:
                    from .._private.argdigest import digest_selection_and_syntax

                    sel, syntax = digest_selection_and_syntax(
                        sel,
                        syntax="MolSysMT",
                        caller="molsysviewer.viewer.presets.resolve_user_preset",
                    )
                    new_rule["atom_indices"] = list(
                        msm.select(view._molsys, selection=sel, syntax=syntax, skip_digestion=True)  # noqa: SLF001
                    )
                except Exception:
                    raise ValueError(f"Unable to resolve selection '{sel}' for user preset '{preset}'")
        rules.append(new_rule)

    return {
        "name": key,
        "base": cfg.get("base"),
        "options": cfg.get("options") or {},
        "rules": rules,
    }


__all__ = [
    "ALLOWED_PRESETS",
    "PRESET_ALIASES",
    "normalize_representation_preset",
    "resolve_user_preset",
]
