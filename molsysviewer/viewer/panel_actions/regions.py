from __future__ import annotations

from typing import Any, Mapping

from ..._pyunitwizard import puw


def _region(view: Any, content: Mapping[str, Any], action: str):
    tag = content.get("tag")
    if not isinstance(tag, str) or tag.strip() not in view._regions:
        raise ValueError(f"No region found with tag {tag!r}.")
    return view._regions[tag.strip()]


def create_region_from_query(view: Any, content: Mapping[str, Any]) -> None:
    expression = content.get("expression")
    if expression is None or (isinstance(expression, str) and not expression.strip()):
        raise ValueError("create_region_from_query requires a non-empty expression.")
    raw_tag = content.get("tag")
    representation = content.get("representation")
    if representation is None:
        representation = "inherit"
    region = view._new_region_impl(
        selection=expression,
        syntax=str(content.get("syntax") or "MolSysMT"),
        tag=raw_tag.strip() if isinstance(raw_tag, str) and raw_tag.strip() else None,
        representation=representation,
        skip_digestion=True,
    )
    preset = content.get("preset")
    if isinstance(preset, str) and preset.strip():
        region.set_representation(preset=preset.strip(), skip_digestion=True)


def make_regions_by(view: Any, content: Mapping[str, Any]) -> None:
    selection = content.get("selection", "all")
    if isinstance(selection, str) and selection.strip().lower() == "active":
        selection = list(view.active_selection.atom_indices)
    regions = view.make_regions_by(
        str(content.get("element") or "").strip().lower(),
        selection=selection,
        representation=content.get("representation"),
        skip_digestion=True,
    )
    preset = content.get("preset")
    if isinstance(preset, str) and preset.strip():
        for region in regions.values():
            region.set_representation(preset=preset.strip(), skip_digestion=True)


def show_only_region(view: Any, content: Mapping[str, Any]) -> None:
    _region(view, content, "show_only_region").show_only(skip_digestion=True)


def raise_region_to_front(view: Any, content: Mapping[str, Any]) -> None:
    _region(view, content, "raise_region_to_front").raise_to_front(skip_digestion=True)


def send_region_to_back(view: Any, content: Mapping[str, Any]) -> None:
    _region(view, content, "send_region_to_back").send_to_back(skip_digestion=True)


def create_complementary_region(view: Any, content: Mapping[str, Any]) -> None:
    raw_tag = content.get("new_tag")
    _region(view, content, "create_complementary_region").new_complementary_region(
        tag=raw_tag.strip() if isinstance(raw_tag, str) and raw_tag.strip() else None,
        skip_digestion=True,
    )


def compose_regions(view: Any, content: Mapping[str, Any]) -> None:
    left = _region(view, {"tag": content.get("tag_a")}, "compose_regions")
    raw_operands = content.get("operand_tags", content.get("tag_b"))
    operand_tags = [raw_operands] if isinstance(raw_operands, str) else list(raw_operands or [])
    operands = []
    for tag in operand_tags:
        if not isinstance(tag, str) or tag.strip() not in view._regions:
            raise ValueError(f"No region found with tag {tag!r}.")
        if tag.strip() != left.tag:
            operands.append(view._regions[tag.strip()])
    if not operands:
        raise ValueError("compose_regions requires at least one operand region.")
    raw_new_tag = content.get("new_tag")
    new_tag = raw_new_tag.strip() if isinstance(raw_new_tag, str) and raw_new_tag.strip() else None
    overwrite = bool(content.get("overwrite", False))
    operation_tag = view._unique_region_tag(f"{new_tag}__compose") if overwrite and new_tag in view._regions else new_tag
    operation = str(content.get("op") or "").strip().lower()
    if operation == "union":
        result = left.union(*operands, tag=operation_tag, skip_digestion=True)
    elif operation == "intersection":
        result = left.intersection(*operands, tag=operation_tag, skip_digestion=True)
    elif operation == "difference":
        result = left.difference(*operands, tag=operation_tag, skip_digestion=True)
    else:
        raise ValueError(f"Unsupported region composition operation: {operation!r}.")
    if overwrite and new_tag in view._regions:
        view._regions[new_tag].delete(skip_digestion=True)
        result.rename(new_tag, skip_digestion=True)


def reset_region_representation(view: Any, content: Mapping[str, Any]) -> None:
    _region(view, content, "reset_region_representation").reset_representation(skip_digestion=True)


def color_region_by_attribute(view: Any, content: Mapping[str, Any]) -> None:
    attribute = content.get("attribute")
    if not isinstance(attribute, str) or not attribute.strip():
        raise ValueError("color_region_by_attribute requires a non-empty attribute.")
    _region(view, content, "color_region_by_attribute").set_color_by_attribute(
        attribute.strip(),
        element=str(content.get("element") or "atom"),
        palette=content.get("palette", "viridis"),
        value_range=content.get("value_range"),
        replace=bool(content.get("replace", False)),
        skip_digestion=True,
    )


def reset_region_colors(view: Any, content: Mapping[str, Any]) -> None:
    _region(view, content, "reset_region_colors").reset_colors(skip_digestion=True)


def duplicate_region(view: Any, content: Mapping[str, Any]) -> None:
    raw_tag = content.get("new_tag")
    _region(view, content, "duplicate_region").duplicate(
        tag=raw_tag.strip() if isinstance(raw_tag, str) and raw_tag.strip() else None,
        skip_digestion=True,
    )


def show_all_regions(view: Any, content: Mapping[str, Any]) -> None:
    del content
    view.regions.show_all(skip_digestion=True)


def hide_all_regions(view: Any, content: Mapping[str, Any]) -> None:
    del content
    view.regions.hide_all(skip_digestion=True)


def set_layer_visibility(view: Any, content: Mapping[str, Any]) -> None:
    tag = content.get("tag")
    if not isinstance(tag, str) or tag.strip() not in view._layers:
        raise ValueError(f"No layer found with tag {tag!r}.")
    layer = view._layers[tag.strip()]
    hidden = content.get("hidden")
    if hidden is None:
        hidden = not bool(getattr(layer, "_hidden", False))
    (layer.hide if bool(hidden) else layer.show)(skip_digestion=True)


def _layer(view: Any, content: Mapping[str, Any], action: str):
    tag = content.get("tag")
    if not isinstance(tag, str) or tag.strip() not in view._layers:
        raise ValueError(f"No layer found with tag {tag!r}.")
    return view._layers[tag.strip()]


def create_layer(view: Any, content: Mapping[str, Any]) -> None:
    tag = content.get("tag")
    if not isinstance(tag, str) or not tag.strip():
        raise ValueError("create_layer requires a non-empty tag.")
    view.layers.add(tag.strip(), skip_digestion=True)


def rename_layer(view: Any, content: Mapping[str, Any]) -> None:
    new_tag = content.get("new_tag")
    if not isinstance(new_tag, str) or not new_tag.strip():
        raise ValueError("rename_layer requires a non-empty new_tag.")
    view.layers.set_tag(_layer(view, content, "rename_layer").tag, new_tag.strip(), skip_digestion=True)


def _layer_member(view: Any, content: Mapping[str, Any], action: str):
    kind = content.get("member_kind")
    tag = content.get("member_tag")
    if kind not in {"region", "annotation", "measurement", "shape"}:
        raise ValueError(f"{action} requires a valid member_kind.")
    if not isinstance(tag, str) or not tag.strip():
        raise ValueError(f"{action} requires a non-empty member_tag.")
    tag = tag.strip()
    if kind == "region":
        member = view.regions.get(tag)
    else:
        manager = {
            "annotation": view.annotations,
            "measurement": view.measurements,
            "shape": view.shapes,
        }[kind]
        member = manager.get(tag, skip_digestion=True)
    if member is None:
        raise ValueError(f"No {kind} found with tag {tag!r}.")
    return kind, member


def add_member_to_layer(view: Any, content: Mapping[str, Any]) -> None:
    layer = _layer(view, {"tag": content.get("layer")}, "add_member_to_layer")
    kind, member = _layer_member(view, content, "add_member_to_layer")
    if kind == "region":
        member.set_layer(layer, skip_digestion=True)
    else:
        layer.attach(member)


def remove_member_from_layer(view: Any, content: Mapping[str, Any]) -> None:
    layer = _layer(view, {"tag": content.get("layer")}, "remove_member_from_layer")
    kind, member = _layer_member(view, content, "remove_member_from_layer")
    if kind == "region":
        if member.layer != layer.tag:
            raise ValueError(f"Region {member.tag!r} is not a member of layer {layer.tag!r}.")
        member.remove_from_layer(skip_digestion=True)
    else:
        layer.detach(member)


def ungroup_layer(view: Any, content: Mapping[str, Any]) -> None:
    _layer(view, content, "ungroup_layer").ungroup(skip_digestion=True)


def delete_layer_and_contents(view: Any, content: Mapping[str, Any]) -> None:
    _layer(view, content, "delete_layer_and_contents").delete(skip_digestion=True)


def get_region_details(view: Any, content: Mapping[str, Any]) -> None:
    region = _region(view, content, "get_region_details")
    center = region.get_center(structure_indices=[view.current_structure_index], skip_digestion=True)
    view._send_runtime_only({
        "op": "region_details",
        "request_id": content.get("request_id"),
        "tag": region.tag,
        "atom_count": len(region.atom_indices or ()),
        "group_count": len(region._scoped_indices_for_element("group") or []),
        "chain_count": len(region._scoped_indices_for_element("chain") or []),
        "center_nm": puw.get_value(center, to_unit="nm").tolist(),
        "structure_index": view.current_structure_index,
        "provenance": dict(region.provenance),
        "order": int(region.order),
        "mode": region.mode,
        "broken": bool(region.provenance.get("broken")),
    })


def toggle_region_visibility(view: Any, content: Mapping[str, Any]) -> None:
    region = _region(view, content, "toggle_region_visibility")
    (region.show if region.hidden else region.hide)(skip_digestion=True)


def delete_region(view: Any, content: Mapping[str, Any]) -> None:
    _region(view, content, "delete_region").delete(skip_digestion=True)


def rename_region(view: Any, content: Mapping[str, Any]) -> None:
    new_tag = content.get("new_tag")
    if not isinstance(new_tag, str) or not new_tag.strip():
        raise ValueError("rename_region requires non-empty new_tag.")
    _region(view, content, "rename_region").rename(new_tag.strip(), skip_digestion=True)


def set_region_representation(view: Any, content: Mapping[str, Any]) -> None:
    params = content.get("params")
    _region(view, content, "set_region_representation").set_representation(
        representation=content.get("representation"),
        preset=content.get("preset"),
        skip_digestion=True,
        **(params if isinstance(params, dict) else {}),
    )


HANDLERS = {
    "create_region_from_query": create_region_from_query,
    "make_regions_by": make_regions_by,
    "show_only_region": show_only_region,
    "raise_region_to_front": raise_region_to_front,
    "send_region_to_back": send_region_to_back,
    "create_complementary_region": create_complementary_region,
    "compose_regions": compose_regions,
    "reset_region_representation": reset_region_representation,
    "color_region_by_attribute": color_region_by_attribute,
    "reset_region_colors": reset_region_colors,
    "duplicate_region": duplicate_region,
    "show_all_regions": show_all_regions,
    "hide_all_regions": hide_all_regions,
    "set_layer_visibility": set_layer_visibility,
    "create_layer": create_layer,
    "rename_layer": rename_layer,
    "add_member_to_layer": add_member_to_layer,
    "remove_member_from_layer": remove_member_from_layer,
    "ungroup_layer": ungroup_layer,
    "delete_layer_and_contents": delete_layer_and_contents,
    "get_region_details": get_region_details,
    "toggle_region_visibility": toggle_region_visibility,
    "delete_region": delete_region,
    "rename_region": rename_region,
    "set_region_representation": set_region_representation,
}
