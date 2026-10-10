"""Validated scene batches; consumers retain molecular selections and analyses."""


def batch_scene_objects(view, content):
    domain = content.get("domain")
    operation = content.get("operation")
    managers = {
        "regions": view.regions,
        "selections": view.selections,
        "annotations": view.annotations,
        "measurements": view.measurements,
        "shapes": view.shapes,
        "interactions": view.interactions,
        "layers": view.layers,
    }
    if domain not in managers:
        raise ValueError("Unknown Studio batch domain.")
    allowed = {"delete"} if domain == "selections" else {"show", "hide", "delete"}
    if domain == "layers":
        allowed = {"show", "hide", "ungroup"}
    if operation not in allowed:
        raise ValueError("Unsupported batch operation for this domain.")
    tags = content.get("tags")
    if not isinstance(tags, list) or not tags or any(not isinstance(tag, str) or not tag for tag in tags):
        raise ValueError("Mark at least one current item.")
    if len(set(tags)) != len(tags):
        raise ValueError("A batch must not repeat items.")
    manager = managers[domain]
    current_tags = set(manager.tags(skip_digestion=True)) if domain not in {"regions", "layers"} else None
    # Resolve the complete target set before a mutation or history checkpoint.
    for tag in tags:
        if domain in {"regions", "layers"}:
            item = manager.get(tag)
            if item is None:
                raise ValueError(f"Item {tag!r} no longer exists.")
            if domain == "layers" and item.provenance != "user":
                raise ValueError("Only user layers can be managed in a Studio batch.")
        elif tag not in current_tags:
            raise ValueError(f"Item {tag!r} no longer exists.")
    _apply_batch(view, manager, domain, operation, tags)


def _apply_batch(view, manager, domain, operation, tags):
    """One existing scene-history boundary covers the whole validated batch."""
    with view.history._atomic_operation(("studio-batch", domain, operation)):
        for tag in tags:
            if domain in {"regions", "layers"}:
                getattr(manager[tag], operation)(skip_digestion=True)
            else:
                getattr(manager, operation)(tag, skip_digestion=True)
