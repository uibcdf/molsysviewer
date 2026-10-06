"""Studio actions use the same public interaction workflows as notebooks."""

from __future__ import annotations

from ...scene_history import records_scene_history
from .scene_objects import _tag


def create_interaction(view, content):
    try:
        _create_interaction(view, content)
    except Exception as exc:
        view._send_runtime_only(
            {
                "op": "interaction_action_result",
                "request_id": content.get("request_id"),
                "ok": False,
                "error_message": str(exc),
            }
        )
        raise
    else:
        view._send_runtime_only(
            {
                "op": "interaction_action_result",
                "request_id": content.get("request_id"),
                "ok": True,
                "analysis_name": content.get("analysis_name"),
            }
        )


def _create_interaction(view, content):
    source = content.get("source", "stored")
    name = content.get("analysis_name")
    if source == "calculate":
        calculation = dict(content.get("calculation") or {})
        kind = calculation.pop("kind", "hbond")
        from ..._private.interaction_families import FAMILIES

        if kind not in FAMILIES:
            raise ValueError("Unknown interaction family.")
        had_parameters = "parameters" in calculation
        parameters = calculation.pop("parameters", {})
        if not isinstance(parameters, dict) or not all(isinstance(key, str) for key in parameters):
            raise ValueError("Interaction parameters must be an object with string keys.")
        owned = {
            "name",
            "selection",
            "selection_2",
            "structure_indices",
            "pbc",
            "syntax",
            "skip_digestion",
            "output_type",
            "molecular_system",
            "molecular_system_2",
            "structure_indices_2",
        }
        if parameters.keys() & owned or parameters.keys() & calculation.keys():
            raise ValueError("Scientific parameters cannot override calculation axes or output.")
        calculation.update(parameters)
        family, function, _, _ = FAMILIES[kind]
        # Retain the existing Studio Buch request while exposing its explicit
        # public wrapper. Modern H-bond methods use the provider's named getter.
        method = calculation.get("method", "buch" if kind == "hbond" and not had_parameters else None)
        if kind == "hbond" and method in {"buch", "luzard_chandler"}:
            function = f"get_{method}_hbonds"
            calculation.pop("method", None)
        elif calculation.get("selection_2") is not None:
            calculation.setdefault("selection_mode", "between")
        getter = getattr(getattr(view.interactions, family), function)
        getter(name=name, **calculation)
    elif source == "file":
        view.interactions.load(
            content.get("filename"),
            analysis_name=content.get("file_analysis_name"),
            name=name,
            assume_aligned=content.get("assume_aligned", False),
            atom_indices=content.get("atom_indices"),
            structure_indices=content.get("structure_indices"),
        )
    elif source != "stored":
        raise ValueError("Unknown interaction source.")
    try:
        view.interactions.add(
            name,
            tag=content.get("tag") or None,
            layer_tag=content.get("layer_tag") or None,
            **dict(content.get("filter") or {}),
        )
    except Exception as exc:
        if source != "stored":
            raise ValueError(f"Analysis {name!r} was stored; creating its visual set failed: {exc}") from exc
        raise


def edit_interaction(view, content):
    obj = view.interactions[_tag(content, "edit_interaction")]
    import math

    from ...colors import normalize_color

    if "filter" in content:
        f = content["filter"]
        view.interactions._filter(
            obj.analysis_name,
            f.get("selection", "all"),
            f.get("selection_2"),
            f.get("mode", "involving_selection"),
            f.get("exclusive", False),
            f.get("structure_indices", "all"),
            f.get("interaction_types"),
            f.get("syntax", "MolSysMT"),
        )
    if "color" in content:
        normalize_color(content["color"])
    for key, lower, upper in (("alpha", 0, 1), ("radius_nm", 0, math.inf)):
        if key in content:
            value = content[key]
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
                or not lower <= value <= upper
                or (key == "radius_nm" and value == 0)
            ):
                raise ValueError(f"Invalid interaction {key}.")
    if content.get("new_tag"):
        view._tag_managers["interaction"].validate(content["new_tag"], current_tag=obj.tag)

    if "radius_nm" in content and content.get("radius_unit") != "nm":
        raise ValueError("Interaction radius_nm requires an explicit nm radius_unit.")

    # The outer checkpoint makes a form submission one undoable operation.
    @records_scene_history
    def apply(view):
        if content.get("new_tag"):
            obj.set_tag(content["new_tag"])
        if content.get("layer_tag"):
            obj.set_layer_tag(content["layer_tag"])
        if "filter" in content:
            obj.set_filter(**content["filter"])
        if "color" in content:
            obj.set_color(content["color"])
        if "alpha" in content:
            obj.set_alpha(content["alpha"])
        if "radius_nm" in content:
            obj.set_radius(f"{content['radius_nm']} nm")

    apply(view)


def inspect_interaction(view, content):
    from ...interactions import _to_plain

    result = view.interactions.inspect(
        _tag(content, "inspect_interaction"),
        structure_index=content.get("frame"),
        offset=content.get("offset", 0),
        limit=50,
    )
    view._send_runtime_only(
        {"op": "interaction_inspection", "request_id": content.get("request_id"), "result": _to_plain(result)}
    )


def toggle_interaction_visibility(view, content):
    obj = view.interactions[_tag(content, "toggle_interaction_visibility")]
    (obj.show if obj._hidden else obj.hide)()


def delete_interaction(view, content):
    view.interactions.delete(_tag(content, "delete_interaction"))


def focus_interaction(view, content):
    view.interactions[_tag(content, "focus_interaction")].focus()


def show_all_interactions(view, content):
    view.interactions.show_all()


def hide_all_interactions(view, content):
    view.interactions.hide_all()


def delete_interaction_analysis(view, content):
    view.interactions.delete_analysis(content.get("analysis_name"))


def select_interaction_observation(view, content):
    view.interactions.select_observation(
        _tag(content, "select_interaction_observation"),
        content.get("occurrence_index"),
        structure_index=content.get("frame"),
        analysis_revision=content.get("analysis_revision"),
        query_revision=content.get("query_revision"),
    )


def focus_interaction_observation(view, content):
    view.interactions.focus_observation(
        _tag(content, "focus_interaction_observation"),
        content.get("occurrence_index"),
        structure_index=content.get("frame"),
        analysis_revision=content.get("analysis_revision"),
        query_revision=content.get("query_revision"),
    )


HANDLERS = {
    name: globals()[name]
    for name in (
        "create_interaction",
        "edit_interaction",
        "inspect_interaction",
        "toggle_interaction_visibility",
        "delete_interaction",
        "focus_interaction",
        "show_all_interactions",
        "hide_all_interactions",
        "delete_interaction_analysis",
        "select_interaction_observation",
        "focus_interaction_observation",
    )
}
