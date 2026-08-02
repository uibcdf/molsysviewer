from __future__ import annotations

import json
from typing import Any


class ExportMixin:
    def _build_export_messages(self) -> list[dict]:
        messages = [self._with_export_layer_tag(msg) for msg in self._clean_message_history()]
        existing_measurements = {
            (msg.get("op"), self._tag_from_message(msg))
            for msg in messages
            if msg.get("op") in {"add_distance_measurement", "add_angle_measurement", "add_dihedral_measurement"}
        }
        for msg in self._measurement_history:
            key = (msg.get("op"), self._tag_from_message(msg))
            if key in existing_measurements:
                continue
            messages.append(self._with_export_layer_tag(msg))
            existing_measurements.add(key)
        existing_scene_look = {
            self._SCENE_LOOK_KEYS.get(msg.get("op"))
            for msg in messages
            if msg.get("op") in self._SCENE_LOOK_KEYS
        }
        for key, msg in self._scene_look.items():
            if key not in existing_scene_look:
                messages.append(dict(msg))
                existing_scene_look.add(key)
        for msg in self._player_replay_messages():
            messages.append(msg)
        if self._current_figure_spec:
            messages.append(dict(self._current_figure_spec))
        summary_message = self._build_addon_runtime_summary_message()
        insert_at = len(messages)
        if insert_at > 0 and messages[-1].get("op") == "set_camera_snapshot":
            insert_at -= 1
        messages.insert(insert_at, summary_message)
        if self._last_camera_snapshot:
            messages.append(
                {
                    "op": "set_camera_snapshot",
                    "snapshot": self._last_camera_snapshot,
                    "duration_ms": 0,
                }
            )
        return messages

    def _with_export_layer_tag(self, msg: dict) -> dict:
        tag = self._tag_from_message(msg)
        kind = self._kind_from_message(msg)
        if not isinstance(tag, str) or kind not in {"shape", "annotation", "measurement", "section"}:
            return dict(msg)
        obj = self._scene_objects.get((kind, tag))
        if obj is None:
            return dict(msg)
        layer_tag = getattr(obj, "layer_tag", None)
        if not isinstance(layer_tag, str) or layer_tag.strip() == "":
            return dict(msg)
        updated = dict(msg)
        options = updated.get("options")
        if isinstance(options, dict):
            options = dict(options)
        else:
            options = {}
        options["layer_tag"] = layer_tag
        updated["options"] = options
        return updated

    def _clean_message_history(self) -> list[dict]:
        deleted_dead_layer_tags = {
            (msg.get("kind"), msg.get("tag"))
            for msg in self._message_history
            if msg.get("op") == "delete_layer"
            and isinstance(msg.get("tag"), str)
            and msg.get("kind") != "layer"
            and (msg.get("kind"), msg.get("tag")) not in self._scene_objects
        }
        dead_layer_ops = {
            "add_label",
            "update_label",
            "create_layer",
            "show_layer",
            "hide_layer",
            "delete_layer",
        }
        cleaned: list[dict] = []
        for msg in self._message_history:
            if (
                msg.get("op") in dead_layer_ops
                and (self._kind_from_message(msg), self._tag_from_message(msg)) in deleted_dead_layer_tags
            ):
                continue
            if msg.get("op") == "update_visibility":
                opts = msg.get("options") or {}
                vis = opts.get("visible_atom_indices")
                if vis is None or vis == []:
                    continue
                if isinstance(vis, list) and vis == list(range(len(vis))):
                    continue
            cleaned.append(self._materialize_molecular_projection(msg))
        return cleaned

    def _json_for_html_script(self, obj: Any) -> str:
        text = json.dumps(obj, separators=(",", ":"))
        return (
            text.replace("&", "\\u0026")
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029")
        )


__all__ = ["ExportMixin"]
