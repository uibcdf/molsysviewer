from __future__ import annotations


class HistoryMixin:
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

    def _record_shape_message(self, msg: dict) -> None:
        op = msg.get("op")
        if not isinstance(op, str):
            return

        if op == "delete_layer":
            cleared_tag = msg.get("tag")
            if not isinstance(cleared_tag, str):
                return
            self._shape_history = [m for m in self._shape_history if self._tag_from_message(m) != cleared_tag]
            return

        if op == "set_layer_tag":
            old_tag = msg.get("tag")
            new_tag = msg.get("new_tag")
            if not isinstance(old_tag, str) or not isinstance(new_tag, str):
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
            if not isinstance(cleared_tag, str):
                return
            self._annotation_history = [m for m in self._annotation_history if self._tag_from_message(m) != cleared_tag]
            return

        if op == "set_layer_tag":
            old_tag = msg.get("tag")
            new_tag = msg.get("new_tag")
            if not isinstance(old_tag, str) or not isinstance(new_tag, str):
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
            if not isinstance(cleared_tag, str):
                return
            self._measurement_history = [m for m in self._measurement_history if self._tag_from_message(m) != cleared_tag]
            return

        if op == "set_layer_tag":
            old_tag = msg.get("tag")
            new_tag = msg.get("new_tag")
            if not isinstance(old_tag, str) or not isinstance(new_tag, str):
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

    def _send(self, msg: dict) -> None:
        self._message_history.append(msg)
        self._record_shape_message(msg)
        self._record_annotation_message(msg)
        self._record_measurement_message(msg)
        self._record_selection_message(msg)
        if self._ready:
            self.widget.send(msg)
        else:
            self._pending_messages.append(msg)

    def _send_runtime_only(self, msg: dict) -> None:
        if self._ready:
            self.widget.send(msg)

    def _send_replay(self, msg: dict) -> None:
        self._message_history.append(msg)
        if self._ready:
            self.widget.send(msg)
        else:
            self._pending_messages.append(msg)

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
