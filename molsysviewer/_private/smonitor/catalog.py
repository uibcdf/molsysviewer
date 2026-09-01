from __future__ import annotations

from pathlib import Path

from .meta import DOC_URL, ISSUES_URL, API_URL

PACKAGE_ROOT = Path(__file__).resolve().parents[2]

META = {
    "doc_url": DOC_URL,
    "issues_url": ISSUES_URL,
    "api_url": API_URL,
}

CATALOG = {
    "argument_error": {
        "code": "MOLSYSVIEWER-ARGUMENT-ERROR",
        "source": "molsysviewer.argument",
        "category": "argument",
        "level": "ERROR",
    },
    "file_already_handled": {
        "code": "MOLSYSVIEWER-FILE-ALREADY-HANDLED",
        "source": "molsysviewer.files",
        "category": "io",
        "level": "ERROR",
    },
    "iterator_error": {
        "code": "MOLSYSVIEWER-ITERATOR-ERROR",
        "source": "molsysviewer.iterator",
        "category": "iteration",
        "level": "ERROR",
    },
    "library_not_found": {
        "code": "MOLSYSVIEWER-LIBRARY-NOT-FOUND",
        "source": "molsysviewer.dependencies",
        "category": "dependency",
        "level": "ERROR",
    },
    "molecular_system_needed": {
        "code": "MOLSYSVIEWER-MOLECULAR-SYSTEM-NEEDED",
        "source": "molsysviewer.molecular_system",
        "category": "molecular_system",
        "level": "ERROR",
    },
    "molecular_systems_needed": {
        "code": "MOLSYSVIEWER-MOLECULAR-SYSTEMS-NEEDED",
        "source": "molsysviewer.molecular_system",
        "category": "molecular_system",
        "level": "ERROR",
    },
    "not_compatible_conversion": {
        "code": "MOLSYSVIEWER-NOT-COMPATIBLE-CONVERSION",
        "source": "molsysviewer.conversion",
        "category": "conversion",
        "level": "ERROR",
    },
    "not_implemented_conversion": {
        "code": "MOLSYSVIEWER-NOT-IMPLEMENTED-CONVERSION",
        "source": "molsysviewer.conversion",
        "category": "conversion",
        "level": "ERROR",
    },
    "not_implemented_iterator": {
        "code": "MOLSYSVIEWER-NOT-IMPLEMENTED-ITERATOR",
        "source": "molsysviewer.iterator",
        "category": "iteration",
        "level": "ERROR",
    },
    "not_implemented_method": {
        "code": "MOLSYSVIEWER-NOT-IMPLEMENTED-METHOD",
        "source": "molsysviewer.api",
        "category": "api",
        "level": "ERROR",
    },
    "not_supported_form": {
        "code": "MOLSYSVIEWER-NOT-SUPPORTED-FORM",
        "source": "molsysviewer.form",
        "category": "form",
        "level": "ERROR",
    },
    "not_supported_syntax": {
        "code": "MOLSYSVIEWER-NOT-SUPPORTED-SYNTAX",
        "source": "molsysviewer.syntax",
        "category": "syntax",
        "level": "ERROR",
    },
    "not_with_this_form": {
        "code": "MOLSYSVIEWER-NOT-WITH-THIS-FORM",
        "source": "molsysviewer.form",
        "category": "form",
        "level": "ERROR",
    },
    "not_digested_argument": {
        "code": "MOLSYSVIEWER-NOT-DIGESTED-ARGUMENT",
        "source": "molsysviewer.digestion",
        "category": "argument",
        "level": "WARNING",
    },
    "viewer_init_failed": {
        "code": "MOLSYSVIEWER-VIEWER-INIT-FAILED",
        "source": "molsysviewer.viewer",
        "category": "frontend",
        "level": "WARNING",
    },
    "runtime_contract_rejected": {
        "code": "MOLSYSVIEWER-RUNTIME-CONTRACT-REJECTED",
        "source": "molsysviewer.viewer.transport",
        "category": "transport",
        "level": "ERROR",
    },
    "frontend_action_failed": {
        "code": "MOLSYSVIEWER-FRONTEND-ACTION-FAILED",
        "source": "molsysviewer.viewer",
        "category": "frontend",
        "level": "ERROR",
    },
    "dynamic_region_evaluation_over_budget": {
        "code": "MOLSYSVIEWER-DYNAMIC-REGION-EVALUATION-OVER-BUDGET",
        "source": "molsysviewer.viewer.regions",
        "category": "performance",
        "level": "WARNING",
    },
    "structure_scale_over_budget": {
        "code": "MOLSYSVIEWER-STRUCTURE-SCALE-OVER-BUDGET",
        "source": "molsysviewer.loaders",
        "category": "performance",
        "level": "WARNING",
    },
    "state_structure_index_out_of_range": {
        "code": "MOLSYSVIEWER-STATE-STRUCTURE-INDEX-OUT-OF-RANGE",
        "source": "molsysviewer.state",
        "category": "state",
        "level": "WARNING",
    },
    "state_structure_differs": {
        "code": "MOLSYSVIEWER-STATE-STRUCTURE-DIFFERS",
        "source": "molsysviewer.state",
        "category": "state",
        "level": "WARNING",
    },
    "structure_data_stream_fallback": {
        "code": "MOLSYSVIEWER-STRUCTURE-DATA-STREAM-FALLBACK",
        "source": "molsysviewer.viewer.transport",
        "category": "transport",
        "level": "WARNING",
    },
    "camera_stranded_inside_scene": {
        "code": "MOLSYSVIEWER-CAMERA-STRANDED-INSIDE-SCENE",
        "source": "molsysviewer.viewer.camera",
        "category": "rendering",
        "level": "WARNING",
    },
    "binary_transport_unsupported": {
        "code": "MOLSYSVIEWER-BINARY-TRANSPORT-UNSUPPORTED",
        "source": "molsysviewer.standalone_qt",
        "category": "transport",
        "level": "ERROR",
    },
    "addon_load_failed": {
        "code": "MOLSYSVIEWER-ADDON-LOAD-FAILED",
        "source": "molsysviewer.addons",
        "category": "addon",
        "level": "WARNING",
    },
    "addon_lifecycle_failed": {
        "code": "MOLSYSVIEWER-ADDON-LIFECYCLE-FAILED",
        "source": "molsysviewer.addons",
        "category": "addon",
        "level": "WARNING",
    },
    "payload_invalid_coordinates": {
        "code": "MOLSYSVIEWER-PAYLOAD-INVALID-COORDINATES",
        "source": "molsysviewer.loaders.molsysmt",
        "category": "payload",
        "level": "DEBUG",
    },
    "payload_invalid_box_vectors": {
        "code": "MOLSYSVIEWER-PAYLOAD-INVALID-BOX-VECTORS",
        "source": "molsysviewer.loaders.molsysmt",
        "category": "payload",
        "level": "DEBUG",
    },
    "payload_invalid_bond_pairs": {
        "code": "MOLSYSVIEWER-PAYLOAD-INVALID-BOND-PAIRS",
        "source": "molsysviewer.loaders.molsysmt",
        "category": "payload",
        "level": "DEBUG",
    },
    "payload_invalid_bond_indices": {
        "code": "MOLSYSVIEWER-PAYLOAD-INVALID-BOND-INDICES",
        "source": "molsysviewer.loaders.molsysmt",
        "category": "payload",
        "level": "DEBUG",
    },
    "suppressed_exception": {
        "code": "MOLSYSVIEWER-SUPPRESSED-EXCEPTION",
        "source": "molsysviewer.state",
        "category": "diagnostic",
        "level": "WARNING",
    },
    "webgl_context_lost": {
        "code": "MOLSYSVIEWER-WEBGL-CONTEXT-LOST",
        "source": "molsysviewer.viewer",
        "category": "rendering",
        "level": "WARNING",
    },
    "webgl_context_restored": {
        "code": "MOLSYSVIEWER-WEBGL-CONTEXT-RESTORED",
        "source": "molsysviewer.viewer",
        "category": "rendering",
        "level": "INFO",
    },
}

#: One message per catalog entry, keyed the way this file is authored: by the catalog
#: key, not by the code. `CODES` below is derived from it.
#:
#: Until 2026-09-01 this dict *was* `CODES`, and none of its templates ever rendered.
#: SMonitor resolves a template with `self._codes.get(code)` and then reads a
#: per-profile field off it (`manager.py`), so it needs a mapping **from the code
#: string** to a **dict**. This one was keyed by catalog key and held plain strings, so
#: every lookup missed and `message_from_catalog` fell back to the `default_message` its
#: caller passed. Nothing looked broken because every caller passes one -- which is also
#: how it survived: the fallback hid the defect completely, while
#: `devguide/smonitor.md` rule 1 ("zero string hardcoding") was satisfied on paper and
#: defeated in practice.
MESSAGES = {
    "argument_error": "Error in {caller} due to the {argument} argument with value {value}.{detail}",
    "file_already_handled": "The file {filename} is already handled.",
    "iterator_error": "Error in iterator: {detail}.",
    "library_not_found": "The python library {library} was not found. (Caller: {caller})",
    "molecular_system_needed": "A molecular system is needed.",
    "molecular_systems_needed": "Molecular systems are needed.",
    "not_compatible_conversion": "Not compatible conversion.",
    "not_implemented_conversion": "Not implemented conversion.",
    "not_implemented_iterator": "Not implemented iterator.",
    "not_implemented_method": "Not implemented method: {method}.",
    "not_supported_form": "Not supported form: {form}.",
    "not_supported_syntax": "Not supported syntax: {syntax}.",
    "not_with_this_form": "Not with this form.",
    "not_digested_argument": "The argument '{argument}' in '{caller}' has no digester. (Standard: ArgDigest style='package')",
    "structure_scale_over_budget": (
        "This selection materializes {structures} structures of {atoms} atoms, about "
        "{size} of coordinates, over the {budget} budget. Every selected structure is "
        "held in memory, and a canvas popup doubles the renderer-side cost, so the "
        "browser tab may run out of memory. To stay under budget, load a subset, for "
        "example structure_indices=range(0, {structures}, {stride}) ({kept} structures). "
        "Raise the ceiling with molsysviewer.config.set_structure_scale_budget(bytes) if "
        "this machine can hold it."
    ),
    "state_structure_index_out_of_range": (
        "This state was saved at structure {saved_index}, but the loaded system has "
        "{n_structures}. The frame was left where it is rather than moved somewhere the "
        "document did not ask for."
    ),
    "state_structure_differs": (
        "This state was saved from a different system ({saved_atoms} atoms; this one has "
        "{current_atoms}), so its stored atom indices do not address the same atoms here. "
        "Objects that kept a recipe were re-resolved against the loaded system; those that "
        "could not be are marked broken. Check that they landed where you expect."
    ),
    "structure_data_stream_fallback": "The array-native structure stream failed and fell back to JSON: {reason}",
    "camera_stranded_inside_scene": (
        "The camera was left {distance} from its target, inside a scene of radius "
        "{scene_radius} — a viewpoint nobody chose, and the signature of Mol* having "
        "clamped it against bounds derived from a half-built scene "
        "(scene_contracts.md Contract S9). The view will look zoomed into the middle "
        "of the system and the wheel may refuse to zoom out; 'Reset view' recovers "
        "it. Camera authority is meant to prevent this, so seeing it means the "
        "protection is no longer effective — most likely a Mol* upgrade changed one "
        "of the hidden params it relies on."
    ),
    "binary_transport_unsupported": (
        "This control channel cannot deliver AnyWidget-style buffers for "
        "{operation}; use the connector's structural data-plane path."
    ),
    "viewer_init_failed": "Mol* viewer failed to initialize. Reason: {reason}. {message}",
    "runtime_contract_rejected": "Runtime contract rejected a message on {seam}: {reason} ({detail}).",
    "frontend_action_failed": "Frontend action {action} failed while processing {event}: {error_type}: {error_message}",
    "addon_load_failed": "Failed to load add-on module '{module}': {reason}.",
    "payload_invalid_coordinates": "Invalid coordinates in payload: {detail}",
    "payload_invalid_box_vectors": "Invalid box vectors in payload: {detail}",
    "payload_invalid_bond_pairs": "Invalid bond pairs in payload: {detail}",
    "payload_invalid_bond_indices": "Invalid bond indices in payload: {detail}",
}


#: The fields SMonitor reads, one per profile plus the `message` its `dev`/`debug`
#: branch falls back to.
PROFILES_FIELDS = ("user_message", "qa_message", "agent_message", "dev_message", "message")


def _code_entry(template: str) -> dict:
    """One template, every profile.

    SMonitor picks the field by profile and does **not** fall back between them: under
    `qa` it reads `qa_message` and gets an empty string when only `user_message` exists.
    These diagnostics say the same thing to everyone, so the entry is built from one
    string rather than repeating it four times and letting the copies drift.
    """

    return {field: template for field in PROFILES_FIELDS}


#: What SMonitor actually consumes: keyed by the code string, valued by a per-profile
#: dict. Derived, never hand-written -- a second hand-maintained list of the same
#: messages is the drift this repository spends its guards on.
CODES = {
    CATALOG[key]["code"]: _code_entry(template)
    for key, template in MESSAGES.items()
    if key in CATALOG
}

#: Templates whose catalog entry disappeared would be silently unreachable.
_ORPHAN_MESSAGES = sorted(set(MESSAGES) - set(CATALOG))
assert not _ORPHAN_MESSAGES, f"MESSAGES entries with no CATALOG entry: {_ORPHAN_MESSAGES}"

SIGNALS = {
    "molsysviewer.new_view.new_view": {"extra_required": ["load_mode", "syntax", "reused_view", "molecular_system_form"]},
    "molsysviewer.viewer.load": {"extra_required": ["molecular_system"]},
    "molsysviewer.viewer.zoom": {"extra_required": ["selection"]},
    "molsysviewer.viewer.set_controls_visible": {"extra_required": ["visible", "autohide"]},
    "molsysviewer.viewer.set_panel_mode": {"extra_required": ["panel", "expanded"]},
    "molsysviewer.viewer.set_workspace": {"extra_required": ["workspace"]},
    "molsysviewer.viewer.set_workspace_panel": {"extra_required": ["panel", "workspace"]},
    "molsysviewer.viewer.workspace_catalog": {"extra_required": ["current_workspace", "workspace_count"]},
    "molsysviewer.viewer.workspace_panels": {"extra_required": ["workspace"]},
    "molsysviewer.viewer.workspace_runtime": {"extra_required": ["current_workspace", "panel_count"]},
    "molsysviewer.viewer.get_panel_mode_state": {"extra_required": ["pretty"]},
    "molsysviewer.viewer.get_camera_snapshot": {"extra_required": ["pretty"]},
    "molsysviewer.viewer.set_camera_snapshot": {"extra_required": ["duration_ms", "snapshot_keys"]},
    "molsysviewer.viewer.write_html": {"extra_required": ["output_filename", "shared_runtime", "include_popout"]},
    "molsysviewer.exports.image": {"extra_required": ["output_filename", "transparent", "preset"]},
    "molsysviewer.exports.figure": {"extra_required": ["output_filename", "has_figure_spec", "preset"]},
    "molsysviewer.exports.figure_variants": {"extra_required": ["output_directory", "stem", "variant_count"]},
    "molsysviewer.exports.figure_publication_set": {"extra_required": ["output_directory", "stem", "include_current", "has_figure_spec"]},
    "molsysviewer.whole.set_representation": {"extra_required": ["representation", "preset"]},
    "molsysviewer.regions.set_representation": {"extra_required": ["representation", "preset"]},
    "molsysviewer.layers.set_tag": {"extra_required": ["new_tag"]},
}
