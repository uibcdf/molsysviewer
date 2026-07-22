from __future__ import annotations

from typing import Any, Mapping

import molsysmt as msm

from ..._pyunitwizard import puw


def set_whole_representation(view: Any, content: Mapping[str, Any]) -> None:
    params = content.get("params")
    view.whole.set_representation(
        content.get("representation"),
        preset=content.get("preset"),
        skip_digestion=True,
        **(params if isinstance(params, dict) else {}),
    )


def reset_whole_representation(view: Any, content: Mapping[str, Any]) -> None:
    del content
    view.whole.reset_representation(skip_digestion=True)


def set_whole_visibility(view: Any, content: Mapping[str, Any]) -> None:
    visible = content.get("visible")
    target_visible = bool(visible) if visible is not None else not bool(content.get("hidden"))
    (view.whole.show if target_visible else view.whole.hide)(skip_digestion=True)


def focus_whole(view: Any, content: Mapping[str, Any]) -> None:
    del content
    view.whole.focus(skip_digestion=True)


def set_whole_color_scheme(view: Any, content: Mapping[str, Any]) -> None:
    scheme = content.get("scheme")
    if not isinstance(scheme, str) or not scheme.strip():
        raise ValueError("set_whole_color_scheme requires a non-empty scheme.")
    view.whole.set_color_scheme(scheme.strip(), skip_digestion=True)


def color_whole_by_attribute(view: Any, content: Mapping[str, Any]) -> None:
    attribute = content.get("attribute")
    if not isinstance(attribute, str) or not attribute.strip():
        raise ValueError("color_whole_by_attribute requires a non-empty attribute.")
    view.whole.set_color_by_attribute(
        attribute.strip(),
        element=str(content.get("element") or "atom"),
        palette=content.get("palette", "viridis"),
        value_range=content.get("value_range"),
        structure_indices=content.get("structure_indices"),
        replace=bool(content.get("replace", True)),
        skip_digestion=True,
    )


def reset_whole_colors(view: Any, content: Mapping[str, Any]) -> None:
    del content
    view.whole.reset_colors(skip_digestion=True)


def reset_all_colors(view: Any, content: Mapping[str, Any]) -> None:
    del content
    view.reset_all_colors(skip_digestion=True)


def get_whole_details(view: Any, content: Mapping[str, Any]) -> None:
    center = view.whole.get_center(
        structure_indices=[view.current_structure_index],
        skip_digestion=True,
    )
    composition: dict[str, int] = {}
    if view._molsys is not None:
        for key, flag in (
            ("atoms", "n_atoms"),
            ("groups", "n_groups"),
            ("chains", "n_chains"),
            ("molecules", "n_molecules"),
            ("entities", "n_entities"),
        ):
            try:
                composition[key] = int(msm.get(
                    view._molsys,
                    element="system",
                    output_type="values",
                    skip_digestion=True,
                    **{flag: True},
                ))
            except Exception:
                composition[key] = 0
    contains: dict[str, int] = {}
    composed_of: dict[str, bool] = {}
    for token, attribute in view._WHOLE_COMPOSITION_PROBES:
        try:
            contains[token] = int(msm.get(
                view._molsys,
                element="system",
                output_type="values",
                skip_digestion=True,
                **{attribute: True},
            ))
        except Exception:
            contains[token] = 0
        composed_of[token] = bool(view.whole.is_composed_of(skip_digestion=True, **{attribute: True}))
    view._send_runtime_only({
        "op": "whole_details",
        "request_id": content.get("request_id"),
        "atom_count": int(view._molsys.get_n_atoms()) if view._molsys is not None else 0,
        "composition": composition,
        "contains": contains,
        "is_composed_of": composed_of,
        "center_nm": puw.get_value(center, to_unit="nm").tolist(),
        "structure_index": view.current_structure_index,
    })


HANDLERS = {
    "set_whole_representation": set_whole_representation,
    "reset_whole_representation": reset_whole_representation,
    "set_whole_visibility": set_whole_visibility,
    "focus_whole": focus_whole,
    "set_whole_color_scheme": set_whole_color_scheme,
    "color_whole_by_attribute": color_whole_by_attribute,
    "reset_whole_colors": reset_whole_colors,
    "reset_all_colors": reset_all_colors,
    "get_whole_details": get_whole_details,
}
