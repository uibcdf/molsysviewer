from __future__ import annotations

from typing import Any, Tuple

from .argument.selection import digest_selection
from .argument.structure_indices import digest_structure_indices
from .argument.syntax import digest_syntax


def normalize_viewer_caller(caller: str | None) -> str | None:
    """Keep historical viewer caller paths stable after the viewer package split."""
    if not isinstance(caller, str):
        return caller
    if caller.startswith("molsysviewer.viewer.core."):
        return caller.replace("molsysviewer.viewer.core.", "molsysviewer.viewer.", 1)

    # Map any Mixin method to the historical molsysviewer.viewer namespace:
    # e.g., molsysviewer.viewer.molsysmt_interface.get -> molsysviewer.viewer.get
    parts = caller.split(".")
    if len(parts) >= 4 and parts[0] == "molsysviewer" and parts[1] == "viewer":
        mixin_names = {
            "regions", "panel_mode", "load", "visibility", "scene",
            "molsysmt_interface", "state", "interaction", "history", "export", "scene_registry"
        }
        if parts[2] in mixin_names:
            return f"molsysviewer.viewer.{parts[-1]}"

    return caller



def digest_selection_and_syntax(
    selection: Any = "all",
    *,
    syntax: str = "MolSysMT",
    caller: str | None = None,
) -> Tuple[Any, str]:
    """Digest selection + syntax using MolSysMT-compatible rules."""
    normalized_syntax = digest_syntax(syntax, caller=caller)
    digested_selection = digest_selection(selection, syntax=normalized_syntax, caller=caller)
    return digested_selection, normalized_syntax


def digest_selection_inputs(
    selection: Any = "all",
    structure_indices: Any = "all",
    *,
    syntax: str = "MolSysMT",
    caller: str | None = None,
) -> Tuple[Any, Any, str]:
    """Digest selection, structure_indices, and syntax using MolSysMT-compatible rules."""
    normalized_syntax = digest_syntax(syntax, caller=caller)
    digested_selection = digest_selection(selection, syntax=normalized_syntax, caller=caller)
    digested_structure_indices = digest_structure_indices(structure_indices, caller=caller)
    return digested_selection, digested_structure_indices, normalized_syntax
