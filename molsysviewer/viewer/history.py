from __future__ import annotations


class HistoryMixin:
    _SCENE_LOOK_KEYS = {
        "toggle_background": "background",
        "set_background_color": "background",
        "set_fog": "fog",
        "set_lighting": "lighting",
        "set_clip_planes": "clip_planes",
        "set_legend": "legend",
        "set_focus_fade": "focus_fade",
        "set_trajectory_plot": "trajectory_plot",
    }

    def _tag_from_message(self, msg: dict) -> str | None:
        tag = msg.get("tag")
        if isinstance(tag, str) and tag:
            return tag
        options = msg.get("options")
        if isinstance(options, dict):
            opt_tag = options.get("tag")
            if isinstance(opt_tag, str) and opt_tag:
                return opt_tag
        return None

    def _kind_from_message(self, msg: dict) -> str | None:
        kind = msg.get("kind")
        if isinstance(kind, str) and kind:
            return kind
        op = msg.get("op")
        if op == "add_label" or op == "update_label":
            return "annotation"
        if op in {"add_distance_measurement", "add_angle_measurement", "add_dihedral_measurement"}:
            return "measurement"
        if isinstance(op, str) and op.startswith("add_"):
            return "shape"
        return None

    def _rewrite_history_layer_tag(
        self,
        history: list[dict],
        old_tag: str,
        new_tag: str,
        *,
        kind: str | None = None,
    ) -> list[dict]:
        rewritten: list[dict] = []
        for item in history:
            options = item.get("options")
            if (
                not isinstance(options, dict)
                or options.get("layer_tag") != old_tag
                or (kind not in {None, "layer"} and self._kind_from_message(item) != kind)
            ):
                rewritten.append(item)
                continue
            updated = dict(item)
            updated_options = dict(options)
            updated_options["layer_tag"] = new_tag
            updated["options"] = updated_options
            rewritten.append(updated)
        return rewritten

    def _rewrite_scene_layer_histories(self, old_tag: str, new_tag: str, kind: str) -> None:
        if kind in {"layer", "shape"}:
            self._shape_history = self._rewrite_history_layer_tag(self._shape_history, old_tag, new_tag)
        if kind in {"layer", "annotation"}:
            self._annotation_history = self._rewrite_history_layer_tag(self._annotation_history, old_tag, new_tag)
        if kind in {"layer", "measurement"}:
            self._measurement_history = self._rewrite_history_layer_tag(self._measurement_history, old_tag, new_tag)
        self._message_history = self._rewrite_history_layer_tag(
            self._message_history,
            old_tag,
            new_tag,
            kind=kind,
        )

    _REGION_OPS = frozenset({
        "create_region", "set_region_representation",
        "show_region", "hide_region", "delete_region",
    })

    def _record_shape_message(self, msg: dict) -> None:
        op = msg.get("op")
        if not isinstance(op, str):
            return

        if op == "rename_region":
            old_tag = msg.get("tag")
            new_tag = msg.get("new_tag")
            if not isinstance(old_tag, str) or not isinstance(new_tag, str) or old_tag == new_tag:
                self._message_history.pop()
                return
            def _rewrite_region(item: dict) -> dict:
                if self._tag_from_message(item) != old_tag:
                    return item
                if item.get("op") not in self._REGION_OPS:
                    return item
                updated = dict(item)
                updated["tag"] = new_tag
                return updated
            # Rewrite all previous entries; drop the rename_region msg itself (last entry).
            self._message_history = [_rewrite_region(m) for m in self._message_history[:-1]]
            return

        if op == "delete_layer":
            cleared_tag = msg.get("tag")
            kind = msg.get("kind")
            if not isinstance(cleared_tag, str) or kind not in {"shape", "layer"}:
                return
            self._shape_history = [m for m in self._shape_history if self._tag_from_message(m) != cleared_tag]
            return

        if op == "set_layer_tag":
            old_tag = msg.get("tag")
            new_tag = msg.get("new_tag")
            kind = msg.get("kind")
            if not isinstance(old_tag, str) or not isinstance(new_tag, str) or kind not in {"shape", "layer"}:
                return
            self._rewrite_scene_layer_histories(old_tag, new_tag, kind)
            if kind != "shape":
                return
            rewritten: list[dict] = []
            for item in self._shape_history:
                tag = self._tag_from_message(item)
                if tag != old_tag:
                    rewritten.append(item)
                    continue
                updated = dict(item)
                updated["tag"] = new_tag
                options = updated.get("options")
                if isinstance(options, dict):
                    options = dict(options)
                    options["tag"] = new_tag
                    updated["options"] = options
                rewritten.append(updated)
            self._shape_history = rewritten
            return

        if op == "clear_shapes_by_tag":
            cleared_tag = msg.get("tag")
            if cleared_tag is None:
                self._shape_history.clear()
                return
            if not isinstance(cleared_tag, str):
                return
            self._shape_history = [m for m in self._shape_history if self._tag_from_message(m) != cleared_tag]
            return

        if op in {"add_label", "add_distance_measurement", "add_angle_measurement", "add_dihedral_measurement"}:
            return

        if not op.startswith("add_"):
            return

        self._shape_history.append(dict(msg))

    def _record_annotation_message(self, msg: dict) -> None:
        op = msg.get("op")
        if not isinstance(op, str):
            return

        if op == "clear_scene":
            options = msg.get("options")
            if isinstance(options, dict) and bool(options.get("labels")):
                self._annotation_history.clear()
            return

        if op == "delete_layer":
            cleared_tag = msg.get("tag")
            kind = msg.get("kind")
            if not isinstance(cleared_tag, str) or kind not in {"annotation", "layer"}:
                return
            self._annotation_history = [m for m in self._annotation_history if self._tag_from_message(m) != cleared_tag]
            return

        if op == "set_layer_tag":
            old_tag = msg.get("tag")
            new_tag = msg.get("new_tag")
            kind = msg.get("kind")
            if not isinstance(old_tag, str) or not isinstance(new_tag, str) or kind not in {"annotation", "layer"}:
                return
            self._rewrite_scene_layer_histories(old_tag, new_tag, kind)
            if kind != "annotation":
                return
            rewritten: list[dict] = []
            for item in self._annotation_history:
                tag = self._tag_from_message(item)
                if tag != old_tag:
                    rewritten.append(item)
                    continue
                updated = dict(item)
                updated["tag"] = new_tag
                options = updated.get("options")
                if isinstance(options, dict):
                    options = dict(options)
                    options["tag"] = new_tag
                    updated["options"] = options
                rewritten.append(updated)
            self._annotation_history = rewritten
            return

        if op == "update_label":
            updated_tag = self._tag_from_message(msg)
            if updated_tag is None:
                return
            rewritten: list[dict] = []
            for item in self._annotation_history:
                if self._tag_from_message(item) != updated_tag:
                    rewritten.append(item)
                    continue
                updated = dict(item)
                options = updated.get("options")
                if isinstance(options, dict):
                    options = dict(options)
                else:
                    options = {}
                new_options = msg.get("options")
                if isinstance(new_options, dict):
                    if "text" in new_options:
                        options["text"] = new_options["text"]
                    if "atom_indices" in new_options:
                        options["atom_indices"] = new_options["atom_indices"]
                    if "tag" in new_options:
                        options["tag"] = new_options["tag"]
                updated["options"] = options
                rewritten.append(updated)
            self._annotation_history = rewritten
            return

        if op != "add_label":
            return

        self._annotation_history.append(dict(msg))

    def _record_measurement_message(self, msg: dict) -> None:
        op = msg.get("op")
        if not isinstance(op, str):
            return

        if op == "delete_layer":
            cleared_tag = msg.get("tag")
            kind = msg.get("kind")
            if not isinstance(cleared_tag, str) or kind not in {"measurement", "layer"}:
                return
            self._measurement_history = [m for m in self._measurement_history if self._tag_from_message(m) != cleared_tag]
            return

        if op == "set_layer_tag":
            old_tag = msg.get("tag")
            new_tag = msg.get("new_tag")
            kind = msg.get("kind")
            if not isinstance(old_tag, str) or not isinstance(new_tag, str) or kind not in {"measurement", "layer"}:
                return
            self._rewrite_scene_layer_histories(old_tag, new_tag, kind)
            if kind != "measurement":
                return
            rewritten: list[dict] = []
            for item in self._measurement_history:
                tag = self._tag_from_message(item)
                if tag != old_tag:
                    rewritten.append(item)
                    continue
                updated = dict(item)
                updated["tag"] = new_tag
                options = updated.get("options")
                if isinstance(options, dict):
                    options = dict(options)
                    options["tag"] = new_tag
                    updated["options"] = options
                rewritten.append(updated)
            self._measurement_history = rewritten
            return

        if op not in {"add_distance_measurement", "add_angle_measurement", "add_dihedral_measurement"}:
            return

        tag = self._tag_from_message(msg)
        if isinstance(tag, str):
            self._measurement_history = [item for item in self._measurement_history if self._tag_from_message(item) != tag]
        self._measurement_history.append(dict(msg))

    def _record_selection_message(self, msg: dict) -> None:
        op = msg.get("op")
        if not isinstance(op, str):
            return

        if op == "clear_selections":
            self._selection_history.clear()
            return

        if op == "delete_selection":
            cleared_tag = msg.get("tag")
            if not isinstance(cleared_tag, str):
                return
            self._selection_history = [m for m in self._selection_history if m.get("tag") != cleared_tag]
            return

        if op == "set_selection_tag":
            old_tag = msg.get("tag")
            new_tag = msg.get("new_tag")
            if not isinstance(old_tag, str) or not isinstance(new_tag, str):
                return
            rewritten: list[dict] = []
            for item in self._selection_history:
                if item.get("tag") != old_tag:
                    rewritten.append(item)
                    continue
                updated = dict(item)
                updated["tag"] = new_tag
                rewritten.append(updated)
            self._selection_history = rewritten
            return

        if op != "save_selection":
            return

        self._selection_history.append(dict(msg))

    def _record_scene_look_message(self, msg: dict) -> None:
        key = self._SCENE_LOOK_KEYS.get(msg.get("op"))
        if key is not None:
            self._scene_look[key] = dict(msg)

    def _remap_scene_look_message(self, msg: dict, atom_index_map: dict[int, int] | None) -> dict | None:
        if atom_index_map is None or msg.get("op") != "set_focus_fade":
            return dict(msg)
        options = msg.get("options")
        if not isinstance(options, dict):
            return dict(msg)
        focus_atom_indices = options.get("focus_atom_indices")
        if focus_atom_indices is None:
            return dict(msg)
        remapped = self._remap_indices(focus_atom_indices, atom_index_map)
        if not remapped:
            return None
        updated = dict(msg)
        updated_options = dict(options)
        updated_options["focus_atom_indices"] = remapped
        updated["options"] = updated_options
        return updated

    def _send(self, msg: dict) -> None:
        self._message_history.append(msg)
        self._record_shape_message(msg)
        self._record_annotation_message(msg)
        self._record_measurement_message(msg)
        self._record_selection_message(msg)
        self._record_scene_look_message(msg)
        if self._ready:
            self.widget.send(msg)
        else:
            self._pending_messages.append(msg)
            self.widget.initial_messages = list(self._pending_messages)

    def _send_runtime_only(self, msg: dict) -> None:
        if self._ready:
            self.widget.send(msg)

    def _send_replay(self, msg: dict) -> None:
        self._message_history.append(msg)
        if self._ready:
            self.widget.send(msg)
        else:
            self._pending_messages.append(msg)
            self.widget.initial_messages = list(self._pending_messages)

    def _get_shape_message(self, tag: str) -> dict | None:
        for msg in reversed(self._shape_history):
            if self._tag_from_message(msg) == tag:
                return dict(msg)
        return None

    def _replace_shape_message(self, tag: str, new_msg: dict) -> None:
        def is_shape_add(item: dict) -> bool:
            op = item.get("op")
            return (
                isinstance(op, str)
                and op.startswith("add_")
                and op not in {"add_label", "add_distance_measurement", "add_angle_measurement", "add_dihedral_measurement"}
            )

        def rewrite(history: list[dict]) -> list[dict]:
            rewritten: list[dict] = []
            for item in history:
                if self._tag_from_message(item) == tag and is_shape_add(item):
                    rewritten.append(dict(new_msg))
                else:
                    rewritten.append(item)
            return rewritten

        self._shape_history = rewrite(self._shape_history)
        self._message_history = rewrite(self._message_history)


__all__ = ["HistoryMixin"]
