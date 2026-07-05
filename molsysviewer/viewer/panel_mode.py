from __future__ import annotations


import json

import inspect
from typing import Any, Mapping

from smonitor import signal
from .._private.arg_digestion import digest
from .signals import (
    controls_signal_extra as _controls_signal_extra,
    panel_mode_signal_extra as _panel_mode_signal_extra,
    panel_mode_state_query_extra as _panel_mode_state_query_extra,
    workspace_catalog_signal_extra as _workspace_catalog_signal_extra,
    workspace_panel_signal_extra as _workspace_panel_signal_extra,
    workspace_panels_signal_extra as _workspace_panels_signal_extra,
    workspace_runtime_signal_extra as _workspace_runtime_signal_extra,
    workspace_sections_signal_extra as _workspace_sections_signal_extra,
    workspace_signal_extra as _workspace_signal_extra,
    resolve_entry_callable as _resolve_entry_callable,
)


class PanelModeMixin:
    @signal(tags=["viewer", "query"], extra_factory=_panel_mode_state_query_extra)
    def get_panel_mode_state(self, *, pretty: bool = False) -> dict | str | None:
        """Return the last known frontend panel/workspace runtime state.

        Parameters
        ----------
        pretty
            If ``True``, return formatted JSON instead of a dict.
        """
        if self._last_panel_mode_state_event is None:
            return None
        if not pretty:
            return dict(self._last_panel_mode_state_event)
        return json.dumps(self._last_panel_mode_state_event, indent=2, sort_keys=True)

    @signal(tags=["viewer", "controls"], extra_factory=_controls_signal_extra)
    @digest()
    def set_controls_visible(
        self,
        visible: bool,
        *,
        autohide: bool | None = None,
        position: list[str] | tuple[str, str] | None = None,
        position_fullscreen: list[str] | tuple[str, str] | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Show or hide the on-canvas controls. Optionally toggle autohide and positions."""
        try:
            self.widget.show_controls = bool(visible)
            if autohide is not None:
                self.widget.autohide_controls = bool(autohide)
            if position is not None:
                self.widget.controls_position = list(position)
            if position_fullscreen is not None:
                self.widget.controls_position_fullscreen = list(position_fullscreen)
        except Exception:
            pass

    @signal(tags=["viewer", "panel"], extra_factory=_panel_mode_signal_extra)
    @digest()
    def set_panel_mode(
        self,
        panel: str | None = None,
        *,
        expanded: bool = True,
        skip_digestion: bool = False,
    ) -> None:
        """Open/close the shared panel-mode surface."""
        self._send(
            {
                "op": "set_panel_mode",
                "panel": panel,
                "expanded": bool(expanded),
            }
        )

    @signal(tags=["viewer", "panel"], extra_factory=_workspace_signal_extra)
    @digest()
    def set_workspace(
        self,
        workspace: str = "core",
        *,
        skip_digestion: bool = False,
    ) -> None:
        """Select the active workspace in the shared panel-mode runtime."""
        self._send(
            {
                "op": "set_workspace",
                "workspace": workspace,
            }
        )

    @signal(tags=["viewer", "panel"], extra_factory=_workspace_panel_signal_extra)
    @digest()
    def set_workspace_panel(
        self,
        panel: str,
        *,
        workspace: str | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Select the active panel inside the current or given workspace."""
        self._send(
            {
                "op": "set_workspace_panel",
                "panel": panel,
                "workspace": workspace,
            }
        )

    @signal(tags=["viewer", "panel", "query"], extra_factory=_workspace_catalog_signal_extra)
    @digest()
    def workspace_catalog(self, *, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return the current effective workspace catalog visible to the view."""
        workspace_specs = self.addons.workspace_specs(skip_digestion=True)
        panel_specs = self.addons.panel_specs(skip_digestion=True)
        workbench_specs = self.addons.addon_section_specs(skip_digestion=True)
        context_action_specs = self.addons.context_action_specs(skip_digestion=True)
        export_helper_specs = self.addons.export_helper_specs(skip_digestion=True)
        state = self.get_panel_mode_state() or {}
        active_workspace = state.get("workspace") if isinstance(state, dict) else None

        records: list[dict[str, Any]] = [
            {
                "id": "core",
                "title": "Core",
                "subtitle": "Navigate + Workbench",
                "active": active_workspace == "core",
            }
        ]

        for workspace in workspace_specs:
            workspace_id = workspace.get("id")
            addon_name = workspace.get("addon")
            if not isinstance(workspace_id, str) or not isinstance(addon_name, str):
                continue
            panel_count = sum(
                1
                for item in panel_specs
                if item.get("addon") == addon_name and item.get("target", "panel_mode") == "panel_mode"
            )
            workbench_section_count = sum(
                1
                for item in workbench_specs
                if item.get("addon") == addon_name and item.get("target_panel", "addons") == "addons"
            )
            context_action_count = sum(1 for item in context_action_specs if item.get("addon") == addon_name)
            export_helper_count = sum(1 for item in export_helper_specs if item.get("addon") == addon_name)
            total_visible = panel_count + workbench_section_count
            if total_visible <= 0:
                continue

            summary_parts: list[str] = []
            if panel_count > 0:
                summary_parts.append(f"{panel_count} panel{'' if panel_count == 1 else 's'}")
            if workbench_section_count > 0:
                summary_parts.append(f"{workbench_section_count} section{'' if workbench_section_count == 1 else 's'}")
            if context_action_count > 0:
                summary_parts.append(f"{context_action_count} context action{'' if context_action_count == 1 else 's'}")
            if export_helper_count > 0:
                summary_parts.append(f"{export_helper_count} export helper{'' if export_helper_count == 1 else 's'}")

            record = dict(workspace)
            record["subtitle"] = " · ".join(summary_parts)
            record["active"] = workspace_id == active_workspace
            records.append(record)

        return records

    @signal(tags=["viewer", "panel", "query"], extra_factory=_workspace_panels_signal_extra)
    @digest()
    def workspace_panels(
        self,
        workspace: str = "core",
        *,
        skip_digestion: bool = False,
    ) -> list[dict[str, Any]]:
        """Return the visible local panel stack for a workspace."""
        state = self.get_panel_mode_state() or {}
        active_workspace = state.get("workspace") if isinstance(state, dict) else None
        active_panel = state.get("workspace_panel") if isinstance(state, dict) else None
        if workspace == "core":
            return [
                {"id": "navigate", "title": "Navigate", "active": active_workspace == "core" and active_panel == "navigate"},
                {"id": "addons", "title": "Add-ons", "active": active_workspace == "core" and active_panel == "addons"},
            ]

        workspace_specs = self.addons.workspace_specs(skip_digestion=True)
        panel_specs = self.addons.panel_specs(skip_digestion=True)
        addon_name = next(
            (
                item.get("addon")
                for item in workspace_specs
                if item.get("id") == workspace and isinstance(item.get("addon"), str)
            ),
            None,
        )
        if not isinstance(addon_name, str):
            return []

        records: list[dict[str, Any]] = []
        for item in panel_specs:
            if item.get("addon") != addon_name:
                continue
            if item.get("target", "panel_mode") != "panel_mode":
                continue
            records.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "description": item.get("description"),
                    "entry": item.get("entry"),
                    "addon": addon_name,
                    "workspace": workspace,
                    "active": active_workspace == workspace and item.get("id") == active_panel,
                }
            )
        return records

    @signal(tags=["viewer", "panel", "query"], extra_factory=_workspace_sections_signal_extra)
    @digest()
    def workspace_sections(
        self,
        workspace: str = "core",
        *,
        skip_digestion: bool = False,
    ) -> list[dict[str, Any]]:
        """Return the visible workbench sections for a workspace."""
        if workspace == "core":
            return []

        workspace_specs = self.addons.workspace_specs(skip_digestion=True)
        workbench_specs = self.addons.addon_section_specs(skip_digestion=True)
        addon_name = next(
            (
                item.get("addon")
                for item in workspace_specs
                if item.get("id") == workspace and isinstance(item.get("addon"), str)
            ),
            None,
        )
        if not isinstance(addon_name, str):
            return []

        records: list[dict[str, Any]] = []
        for item in workbench_specs:
            if item.get("addon") != addon_name:
                continue
            if item.get("target_panel", "addons") != "addons":
                continue
            section_id = item.get("id")
            title = item.get("title")
            if not isinstance(section_id, str) or not isinstance(title, str):
                continue
            record = dict(item)
            record["workspace"] = workspace
            records.append(record)
        return self._enrich_addon_sections(records)

    @signal(tags=["viewer", "panel", "query"], extra_factory=_workspace_runtime_signal_extra)
    @digest()
    def workspace_runtime(self, *, pretty: bool = False, skip_digestion: bool = False) -> dict[str, Any] | str:
        """Return a notebook-friendly snapshot of the shared workspace runtime."""
        state = self.get_panel_mode_state() or {}
        if not isinstance(state, dict):
            state = {}
        current_workspace = state.get("workspace")
        if not isinstance(current_workspace, str) or current_workspace.strip() == "":
            current_workspace = "core"
        workspaces = self.workspace_catalog(skip_digestion=True)
        current_panels = self.workspace_panels(current_workspace, skip_digestion=True)
        current_sections = self.workspace_sections(current_workspace, skip_digestion=True)
        current_panel = next((item for item in current_panels if item.get("active") is True), None)
        current_workspace_record = next((item for item in workspaces if item.get("id") == current_workspace), None)
        payload = {
            "state": dict(state),
            "workspaces": workspaces,
            "current_workspace": current_workspace,
            "current_workspace_record": current_workspace_record,
            "current_panels": current_panels,
            "current_panel": current_panel,
            "current_sections": current_sections,
        }
        if pretty:
            return json.dumps(payload, indent=2, sort_keys=True)
        return payload

    def _invoke_addon_entry(self, entry: str) -> Any | None:
        candidate = _resolve_entry_callable(entry)
        if candidate is None or not callable(candidate):
            return None
        try:
            signature = inspect.signature(candidate)
        except (TypeError, ValueError):
            signature = None

        if signature is not None and len(signature.parameters) == 0:
            return candidate()

        try:
            return candidate(self)
        except TypeError:
            try:
                return candidate(view=self)
            except TypeError:
                return None

    def _materialize_addon_entry_payload(self, entry: Any) -> dict[str, Any] | None:
        if not isinstance(entry, str) or entry.strip() == "":
            return None
        payload = self._invoke_addon_entry(entry)
        if payload is None:
            return None
        if isinstance(payload, dict):
            return dict(payload)
        return {"value": payload}

    def _enrich_addon_sections(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for item in records:
            record = dict(item)
            payload = self._materialize_addon_entry_payload(record.get("entry"))
            if payload is not None:
                record["runtime_payload"] = payload
                if isinstance(payload.get("key"), str):
                    record["key"] = payload["key"]
                if isinstance(payload.get("item_title"), str):
                    record["item_title"] = payload["item_title"]
                if isinstance(payload.get("item_subtitle"), str):
                    record["item_subtitle"] = payload["item_subtitle"]
            enriched.append(record)
        return enriched

    def _enrich_export_helper_specs(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for item in records:
            record = dict(item)
            payload = self._materialize_addon_entry_payload(record.get("entry"))
            if payload is not None:
                record["runtime_payload"] = payload
            enriched.append(record)
        return enriched

    def _build_addon_runtime_summary_message(self) -> dict[str, Any]:
        addon_names = self.addons.enabled(skip_digestion=True)
        workspace_specs = self.addons.workspace_specs(skip_digestion=True)
        panel_specs = self.addons.panel_specs(skip_digestion=True)
        addon_sections = self._enrich_addon_sections(
            self.addons.addon_section_specs(skip_digestion=True)
        )
        context_action_specs = self.addons.context_action_specs(skip_digestion=True)
        export_helper_specs = self._enrich_export_helper_specs(
            self.addons.export_helper_specs(skip_digestion=True)
        )
        discovery_failures = self.addons.discovery_failures(skip_digestion=True)
        lifecycle_failures = self.addons.lifecycle_failures(skip_digestion=True)
        return {
            "op": "set_addon_runtime_summary",
            "addons": addon_names,
            "addon_records": self.addons.records(skip_digestion=True),
            "workspace_specs": workspace_specs,
            "panel_specs": panel_specs,
            "addon_sections": addon_sections,
            "context_action_specs": context_action_specs,
            "export_helper_specs": export_helper_specs,
            "discovery_failures": discovery_failures,
            "lifecycle_failures": lifecycle_failures,
        }

    def _sync_addons_runtime(self) -> None:
        self._send(self._build_addon_runtime_summary_message())

    def _mount_addon_panel(self, addon_name: str, panel_id: str) -> None:
        self._unmount_addon_panel()
        widget = self.addons.resolve_panel_widget(addon_name, panel_id)
        if widget is None:
            return

        def _routed_send(msg: dict, buffers: Any = None) -> None:
            self._send_runtime_only({
                "op": "addon_panel_message",
                "addon": addon_name,
                "panel": panel_id,
                "content": msg,
            })

        widget.send = _routed_send
        self._active_panel_widget = (addon_name, panel_id, widget)

        widget.on_mount(self)

        ctx = widget._build_viewer_context()
        _routed_send({"type": "context", "context": ctx})

        self._send_runtime_only({
            "op": "mount_addon_panel",
            "addon": addon_name,
            "panel": panel_id,
            "esm": widget._esm,
            "css": getattr(widget, "_css", "") or "",
        })

    def _unmount_addon_panel(self) -> None:
        if self._active_panel_widget is None:
            return
        _, _, widget = self._active_panel_widget
        self._active_panel_widget = None
        try:
            widget.on_unmount(self)
        except Exception:
            pass


PanelModeMixin.__module__ = "molsysviewer.viewer"
for _name, _value in PanelModeMixin.__dict__.items():
    if callable(_value):
        try:
            _value.__module__ = "molsysviewer.viewer"
        except Exception:
            pass

