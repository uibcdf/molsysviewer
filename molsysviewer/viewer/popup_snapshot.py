"""R2 canonical popup scene snapshot — Python-originated, from live state.

`build_popup_scene_snapshot(mode, endpoint)` regenerates the current scene as a
list of ``ViewerMessage`` dicts. It is pure with respect to history and
transport: it never calls ``_send``, never mutates viewer state, never creates a
checkpoint, and never reads ``_message_history`` or ``_build_export_messages()``.
Its size depends only on the live scene, not on interaction count.

It reuses the same live records ``export_state()`` reads, plus the runtime state
that method omits (molecular projection, visibility, frame, scene look). Every
value that leaves the viewer is defensively copied so a consumer cannot mutate
internal state (records, ``_current_molecular_projection``) through the result.
Camera and host-local UI (open panel, scroll) are never part of a live popup
projection; they are ephemeral endpoint state supplied by the host. Static
export is the deliberate exception: Python captures the last live camera before
the host disappears and embeds it in the exported artifact.
"""

from copy import deepcopy

from .._private.smonitor_emit import emit_suppressed_exception
from typing import Any

from .._private.argdigest import digest

# Deterministic order for the coalesced scene-look entries.
_SCENE_LOOK_ORDER = (
    "background",
    "fog",
    "lighting",
    "clip_planes",
    "legend",
    "focus_fade",
    "trajectory_plot",
)

_PANEL_OPS_ALREADY_IN_CANVAS = frozenset({
    "save_selection",
    "set_active_selection",
    "set_measurement_settings",
})


class PopupSnapshotMixin:
    @digest()
    def build_popup_scene_snapshot(
        self,
        mode: str,
        endpoint: Any = None,
        include_molecular: bool = True,
    ) -> list[dict]:
        """Build the canonical popup scene snapshot for ``mode``.

        ``endpoint`` is correlation/routing metadata only; it never changes the
        scientific content of the projection. ``include_molecular`` is set False
        when the molecular generation is delivered out of band on the data plane
        (D4), so the same scene is not also carried as JSON.
        """
        if mode == "canvas":
            return self._build_canvas_snapshot(include_molecular=include_molecular)
        if mode == "panel":
            return self._build_panel_snapshot()
        raise ValueError(f"popup snapshot mode must be 'canvas' or 'panel', got {mode!r}")

    # -- canvas ---------------------------------------------------------------

    def _build_canvas_snapshot(self, include_molecular: bool = True) -> list[dict]:
        messages: list[dict] = []

        # 1. current molecular projection (box/time absent stay absent).
        if include_molecular and self._current_molecular_projection is not None:
            messages.append(
                self._materialize_molecular_projection(self._current_molecular_projection)
            )

        # 2. scene look, deterministic order.
        for key in _SCENE_LOOK_ORDER:
            look = self._scene_look.get(key)
            if look is not None:
                messages.append(deepcopy(look))

        # Hover telemetry is endpoint runtime state, not scene state. Reproject
        # it so a reconnected canvas follows the current Python subscription.
        messages.append({
            "op": "set_hover_telemetry",
            "enabled": bool(self._hover_telemetry_active),
        })

        # 3. whole: representation, then visibility (separate ops).
        #
        # The representation op is emitted only when the whole actually carries
        # one. "Python never expressed an opinion" and "Python explicitly says
        # None" are the same state in the model and *different* on screen:
        # `setWholeRepresentation` clears the baseline representations before
        # applying anything, and with representation/preset both null it adds
        # nothing back, so the whole goes invisible. A host that never sent the
        # op keeps the default representation the frontend built on load.
        # Reproducing the host means staying silent, exactly as it did.
        whole_representation = self._whole_representation_message()
        if self._whole_has_explicit_representation():
            messages.append(whole_representation)
        messages.append(self._whole_visibility_message())

        # 4. user layers before their members.
        user_layers = [layer for layer in self.layers.values() if layer.provenance == "user"]
        user_layers.sort(key=lambda layer: layer.tag)
        for layer in user_layers:
            messages.append({
                "op": "create_layer",
                "tag": layer.tag,
                "kind": layer.kind,
                "meta": deepcopy(dict(layer.meta)),
            })

        # 5. regions in topological/order order; dynamic regions carry the
        #    materialized indices of the current frame (via _create_message).
        regions = [
            region
            for tag, region in self._regions.items()
            if getattr(region, "_active", False)
            and not self._TRANSIENT_REGION_TAG.fullmatch(tag)
            and region.atom_indices is not None
        ]
        regions.sort(key=lambda region: (getattr(region, "order", 0), region.tag))
        for region in regions:
            messages.append(region._create_message())  # noqa: SLF001
            if getattr(region, "_hidden", False):  # noqa: SLF001
                messages.append({"op": "hide_region", "tag": region.tag})

        # 6. shapes, annotations, measurements from live records (deterministic).
        for record in self._scene_object_creation_messages():
            messages.append(record)

        # 7. sections consolidated.
        messages.append({"op": "set_sections", "sections": deepcopy(list(self._section_history))})

        # 8. object and layer visibility, after their members exist. Scene objects
        #    hide through `hide_layer` with their kind, like layers do. Layer
        #    membership is not a separate op: it already travels in the creation
        #    message's `options.layer_tag` (see _scene_object_creation_messages).
        for kind, tag in sorted(self._scene_objects):
            obj = self._scene_objects[(kind, tag)]
            if getattr(obj, "_hidden", False):  # noqa: SLF001
                messages.append({"op": "hide_layer", "tag": tag, "kind": kind})
        for layer in user_layers:
            if getattr(layer, "_hidden", False):  # noqa: SLF001
                messages.append({"op": "hide_layer", "tag": layer.tag, "kind": "layer"})

        # 9. resolved colours, after components exist.
        color_message = self._resolved_colors_message()
        if color_message is not None:
            messages.append(color_message)

        # 10. saved selections and active selection. The selection records are
        #     already complete `save_selection` messages; emit them verbatim.
        for record in self.selections.records(skip_digestion=True):
            messages.append(deepcopy(record))
        messages.append({
            "op": "set_active_selection",
            "atom_indices": list(self.active_selection.atom_indices),
        })

        # 11. measurement settings.
        messages.append({
            "op": "set_measurement_settings",
            **deepcopy(self.measurements.settings(skip_digestion=True)),
        })

        # 12. full visibility (version is a monotonic counter; ignored by the
        #     size invariant).
        if self.atom_mask is not None:
            messages.append({
                "op": "update_visibility",
                "options": {
                    "visible_atom_indices": list(self.visible_atom_indices),
                    "version": self._visibility_version,
                },
            })

        # 13. current frame and playback. The settings are current state; the play
        #     action is only replayed when playback is actually running.
        messages.append({"op": "set_trajectory_frame", "index": int(self._current_structure_index)})
        player = getattr(self, "player", None)
        if player is not None:
            messages.append({
                "op": "set_trajectory_playback",
                "fps": player._fps,              # noqa: SLF001
                "mode": player._mode,            # noqa: SLF001
                "direction": player._direction,  # noqa: SLF001
                "step": player._step_size,       # noqa: SLF001
            })
            if getattr(player, "_is_playing", False):  # noqa: SLF001
                messages.append({"op": "set_trajectory_playback", "action": "play"})

        # 14. camera is host-local ephemeral state, never in the Python snapshot.
        return messages

    # -- panel ----------------------------------------------------------------

    def _build_panel_snapshot(self) -> list[dict]:
        # UI-only projections. No molecular payload, topology, coordinates, or
        # structure-dependent visual operations may appear here.
        messages: list[dict] = [
            {
                "op": "set_region_summaries",
                "regions": self._region_summary_records(),
                "representations": self.representations,
                "presets": self.presets,
            },
            {"op": "set_whole_summary", **self._whole_summary_record()},
            {"op": "set_layer_summaries", "layers": self._layer_summary_records()},
            {"op": "set_annotation_summaries", "annotations": self._annotation_summary_records()},
            {"op": "set_measurement_summaries", "measurements": self._measurement_summary_records()},
            {"op": "set_shape_summaries", "shapes": self._shape_summary_records()},
            {"op": "set_section_summaries", "sections": self._section_summary_records()},
            {
                "op": "set_measurement_settings",
                **deepcopy(self.measurements.settings(skip_digestion=True)),
            },
            {
                "op": "set_active_selection",
                "atom_indices": list(self.active_selection.atom_indices),
            },
            {
                "op": "set_history_state",
                "can_undo": self.history.can_undo(),
                "can_redo": self.history.can_redo(),
            },
            self._build_addon_runtime_summary_message(),
        ]
        # Add-on context items: the only panel projection the projector could not
        # carry, because the sole builder also pushed to the frontend. It is now
        # split, so this stays pure.
        addons = getattr(self, "addons", None)
        if addons is not None and hasattr(addons, "build_context_items"):
            try:
                items = addons.build_context_items(
                    dict(self._last_active_selection_event or {})
                )
            except Exception as exc:
                emit_suppressed_exception(
                    "molsysviewer.viewer.popup_snapshot.addon_context_items",
                    exc,
                    context={"mode": "panel"},
                )
            else:
                messages.append({"op": "set_addon_context_items", "items": items})
        # Saved-selection records are complete `save_selection` messages.
        for record in self.selections.records(skip_digestion=True):
            messages.append(deepcopy(record))
        # Workspace/panel selection as Python last saw it. Truly ephemeral
        # host-local UI (camera, open panel, scroll) is NOT here: the host
        # assembles it as `endpointState`, so Python never becomes its authority.
        panel_state = self._last_panel_mode_state_event
        if isinstance(panel_state, dict):
            workspace = panel_state.get("workspace")
            if isinstance(workspace, str) and workspace:
                messages.append({"op": "set_workspace", "workspace": workspace})
        return deepcopy(messages)

    # -- static export --------------------------------------------------------

    def _build_static_export_snapshot(self) -> list[dict]:
        """Build the canonical, self-contained static-export projection.

        The renderable scene is shared with the canvas-popup projector. Static
        files additionally need the current figure/add-on projections and the
        camera captured from the live host, because no endpoint exists to supply
        them when the file is opened later.
        """
        messages = self._build_canvas_snapshot(include_molecular=True)
        if self._current_figure_spec:
            messages.append(deepcopy(self._current_figure_spec))
        messages.append(deepcopy(self._build_addon_runtime_summary_message()))
        if self._last_camera_snapshot:
            messages.append({
                "op": "set_camera_snapshot",
                "snapshot": deepcopy(self._last_camera_snapshot),
                "duration_ms": 0,
            })
        return messages

    def _build_embedded_runtime_snapshot(
        self,
        *,
        include_molecular: bool = True,
    ) -> list[dict]:
        """Build current state for a live widget attaching or reconnecting.

        The embedded host needs both the renderable canvas scene and Python's
        authoritative panel projections. Camera stays endpoint-local. Panel
        messages already represented by the canvas profile are filtered by op
        so one ready event applies each current-state projection once.
        """
        messages = self._build_canvas_snapshot(include_molecular=include_molecular)
        if self._current_figure_spec:
            messages.append(deepcopy(self._current_figure_spec))
        messages.extend(
            message
            for message in self._build_panel_snapshot()
            if message.get("op") not in _PANEL_OPS_ALREADY_IN_CANVAS
        )
        return messages

    # -- helpers --------------------------------------------------------------

    def _whole_has_explicit_representation(self) -> bool:
        """True when the whole was actually configured from Python.

        A pristine viewer has `representation`, `preset` and `params` all empty:
        whatever is on screen came from the frontend's own default at load time,
        and no `set_whole_representation` was ever sent.
        """
        return bool(
            self.whole.representation is not None
            or self.whole.preset is not None
            or dict(self.whole.params)
        )

    def _whole_representation_message(self) -> dict:
        return {
            "op": "set_whole_representation",
            "representation": self.whole.representation,
            "preset": self.whole.preset,
            "params": deepcopy(dict(self.whole.params)),
        }

    def _whole_visibility_message(self) -> dict:
        if self.whole.visible:
            return {"op": "show_whole", "target": "whole"}
        return {"op": "hide_whole", "target": "whole"}

    def _scene_object_creation_messages(self) -> list[dict]:
        """Current creation messages for shapes, annotations and measurements.

        ``_with_export_layer_tag`` stamps each message with the object's *current*
        layer membership (the record itself may predate a later move), which is
        the established contract for carrying membership on a creation message.
        It is a small pure helper; the journal builder is not involved.
        """
        out: list[dict] = []
        for record in self.shapes.records(skip_digestion=True):
            out.append(self._with_export_layer_tag(deepcopy(record)))
        for record in self.annotations.records(skip_digestion=True):
            out.append(self._with_export_layer_tag(deepcopy(record)))
        for record in self.measurements.records():
            out.append(self._with_export_layer_tag(deepcopy(record)))
        return out

    def _resolved_colors_message(self) -> dict | None:
        resolved = self._resolved_atom_color_map()
        if not resolved:
            return None
        return {
            "op": "set_atom_colors",
            "atom_indices": list(resolved.keys()),
            "colors": list(resolved.values()),
            "replace": True,
        }


__all__ = ["PopupSnapshotMixin"]
