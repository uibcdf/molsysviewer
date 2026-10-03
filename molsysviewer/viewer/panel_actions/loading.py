"""Studio declares loading intent; the public load owner prepares and commits it."""


def load_systems(view, content):
    request_id = content.get("request_id")
    try:
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("Loading requires a nonempty request identifier.")
        source = content.get("molecular_system")
        if not (isinstance(source, str) and source.strip() or
                isinstance(source, (list, tuple)) and source and
                all(isinstance(item, str) and item.strip() for item in source)):
            raise ValueError("Studio sources must be nonempty file paths or PDB IDs.")
        multiple = content.get("multiple", False)
        if not isinstance(multiple, bool):
            raise ValueError("multiple must explicitly be a boolean.")
        mode = content.get("mode", "add")
        if mode not in {"add", "replace", "append_structures"}:
            raise ValueError("Studio loading requires add, replace or append_structures.")
        view.load(
            source, multiple=multiple, mode=mode,
            selection=content.get("selection", "all"),
            structure_indices=content.get("structure_indices", "all"),
            label=content.get("label"), labels=content.get("labels"),
            structure_pairing=content.get("structure_pairing"),
        )
    except Exception as exc:
        view._send_runtime_only({"op": "system_load_result", "request_id": request_id,
                                 "ok": False, "error_message": str(exc)})
        raise
    else:
        view._send_runtime_only({"op": "system_load_result", "request_id": request_id, "ok": True,
                                 "n_atoms": int(view.molsys.get_n_atoms()),
                                 "n_structures": int(view.player.n_structures),
                                 "n_sources": len(view.load_blocks)})
