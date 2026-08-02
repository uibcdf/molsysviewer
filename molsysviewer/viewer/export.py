from __future__ import annotations

import json
from typing import Any


class ExportMixin:
    def _build_export_messages(self) -> list[dict]:
        """Project the current scene for a hostless static artifact.

        Static export is a snapshot, not command replay. Its content and size
        therefore depend on live state only, never on ``_message_history``.
        """
        return self._build_static_export_snapshot()

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
