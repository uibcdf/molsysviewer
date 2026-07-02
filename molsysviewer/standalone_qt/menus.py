from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ..demo import demo
from .utils import (
    _rebuild_qt_html,
    _persist_shell_state,
    _show_status,
    _show_host_error,
    _set_action_shortcut,
    _record_recent_source,
    _recent_section_title,
    _clear_recent_sources,
    _load_recent_source,
    _load_demo_into_qt_host,
    _restore_last_source,
    _send_viewer_message,
    _load_molecular_system_into_qt_host,
    _export_qt_figure,
    _current_source_summary,
    _host_info_message,
)


def _get_helper(name: str) -> Any:
    m = sys.modules.get("molsysviewer.standalone_qt")
    if m is not None and hasattr(m, name):
        return getattr(m, name)
    return globals()[name]


def _install_menu_bar(
    *,
    window,
    webview,
    QUrl,
    QAction,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    html_path: str,
    current_title: str,
    current_state: dict[str, Any],
) -> None:
    menu_bar = window.menuBar()

    file_menu = menu_bar.addMenu("File")
    view_menu = menu_bar.addMenu("View")
    export_menu = menu_bar.addMenu("Export")
    help_menu = menu_bar.addMenu("Help")

    open_file_action = QAction("Open File", window)
    _get_helper("_set_action_shortcut")(open_file_action, "Ctrl+O")

    new_empty_action = QAction("New Empty Host", window)
    _get_helper("_set_action_shortcut")(new_empty_action, "Ctrl+N")

    def _new_empty_host():
        try:
            _get_helper("_load_molecular_system_into_qt_host")(
                None,
                window=window,
                webview=webview,
                current_state=current_state,
                loaded_label=None,
                status_message="Opened empty host.",
            )
        except Exception as exc:
            _get_helper("_show_host_error")(window, QMessageBox, "New Empty Host Failed", f"Could not open empty host: {exc}")

    new_empty_action.triggered.connect(_new_empty_host)
    file_menu.addAction(new_empty_action)

    def _open_file():
        if not hasattr(QFileDialog, "getOpenFileName"):
            _get_helper("_show_status")(window, "Open File is not available in the current Qt runtime.")
            return
        selected, _filter = QFileDialog.getOpenFileName(
            window,
            "Open molecular system",
            "",
            "Molecular systems (*);;All files (*)",
        )
        if not selected:
            return
        try:
            _get_helper("_load_molecular_system_into_qt_host")(
                selected,
                window=window,
                webview=webview,
                current_state=current_state,
                loaded_label=Path(selected).name,
                status_message=f"Loaded file: {Path(selected).name}",
            )
            _get_helper("_record_recent_source")(
                current_state,
                kind="file",
                value=selected,
                loaded_label=Path(selected).name,
            )
            _refresh_recent_menu()
        except Exception as exc:
            _get_helper("_show_host_error")(window, QMessageBox, "Open File Failed", f"Could not load file: {exc}")

    open_file_action.triggered.connect(_open_file)
    file_menu.addAction(open_file_action)

    demo_menu = file_menu.addMenu("Load Demo")
    recent_menu = file_menu.addMenu("Recent")

    def _refresh_recent_menu() -> None:
        if hasattr(recent_menu, "clear"):
            recent_menu.clear()
        elif isinstance(getattr(recent_menu, "actions", None), list):
            recent_menu.actions.clear()
        recent_sources = current_state.get("recent_sources", [])
        if not recent_sources:
            empty_action = QAction("No recent sources", window)
            recent_menu.addAction(empty_action)
            return
        kind_order = ("demo", "file", "pdb_id", "source")
        grouped_sources: dict[str, list[dict[str, Any]]] = {kind: [] for kind in kind_order}
        for recent_entry in recent_sources:
            kind = str(recent_entry.get("kind", "other"))
            grouped_sources.setdefault(kind, []).append(recent_entry)
        for kind in kind_order:
            entries = grouped_sources.get(kind, [])
            if not entries:
                continue
            target_menu = recent_menu.addMenu(_get_helper("_recent_section_title")(kind))
            for recent_entry in entries:
                recent_action = QAction(recent_entry["loaded_label"], window)
                recent_action.triggered.connect(
                    lambda _checked=False, entry=recent_entry: _get_helper("_load_recent_source")(
                        entry,
                        window=window,
                        webview=webview,
                        QUrl=QUrl,
                        html_path=html_path,
                        current_title=current_title,
                        current_state=current_state,
                    )
                )
                target_menu.addAction(recent_action)
        clear_recent_action = QAction("Clear Recent Sources", window)
        clear_recent_action.triggered.connect(
            lambda: (
                _get_helper("_clear_recent_sources")(current_state),
                _get_helper("_persist_shell_state")(current_state, window=window),
                _refresh_recent_menu(),
                _get_helper("_show_status")(window, "Cleared recent sources."),
            )
        )
        recent_menu.addAction(clear_recent_action)
        extra_kinds = [kind for kind in grouped_sources.keys() if kind not in kind_order]
        for kind in sorted(extra_kinds):
            entries = grouped_sources[kind]
            if not entries:
                continue
            target_menu = recent_menu.addMenu(_get_helper("_recent_section_title")(kind))
            for recent_entry in entries:
                recent_action = QAction(recent_entry["loaded_label"], window)
                recent_action.triggered.connect(
                    lambda _checked=False, entry=recent_entry: _get_helper("_load_recent_source")(
                        entry,
                        window=window,
                        webview=webview,
                        QUrl=QUrl,
                        html_path=html_path,
                        current_title=current_title,
                        current_state=current_state,
                    )
                )
                target_menu.addAction(recent_action)
    for demo_name in sorted(demo.keys()):
        demo_action = QAction(demo_name, window)
        demo_action.triggered.connect(
            lambda _checked=False, name=demo_name: (
                _get_helper("_load_demo_into_qt_host")(
                    name,
                    window=window,
                    webview=webview,
                    QUrl=QUrl,
                    html_path=html_path,
                    current_title=current_title,
                    current_state=current_state,
                ),
                _refresh_recent_menu(),
            )
        )
        demo_menu.addAction(demo_action)

    _refresh_recent_menu()

    load_pdbid_action = QAction("Load PDB ID", window)

    def _load_pdbid():
        if not hasattr(QInputDialog, "getText"):
            _get_helper("_show_status")(window, "Load PDB ID is not available in the current Qt runtime.")
            return
        value, accepted = QInputDialog.getText(
            window,
            "Load PDB ID",
            "PDB ID:",
        )
        pdb_id = str(value).strip()
        if not accepted or not pdb_id:
            return
        try:
            _get_helper("_load_molecular_system_into_qt_host")(
                pdb_id,
                window=window,
                webview=webview,
                current_state=current_state,
                loaded_label=pdb_id,
                status_message=f"Loaded PDB ID: {pdb_id}",
            )
            _get_helper("_record_recent_source")(
                current_state,
                kind="pdb_id",
                value=pdb_id,
                loaded_label=pdb_id,
            )
            _refresh_recent_menu()
        except Exception as exc:
            _get_helper("_show_host_error")(window, QMessageBox, "Load PDB ID Failed", f"Could not load PDB ID: {exc}")

    load_pdbid_action.triggered.connect(_load_pdbid)
    file_menu.addAction(load_pdbid_action)

    load_source_action = QAction("Load Source", window)

    def _load_source():
        if not hasattr(QInputDialog, "getText"):
            _get_helper("_show_status")(window, "Load Source is not available in the current Qt runtime.")
            return
        value, accepted = QInputDialog.getText(
            window,
            "Load MolSysMT Source",
            "Source:",
        )
        source_value = str(value).strip()
        if not accepted or not source_value:
            return
        try:
            _get_helper("_load_molecular_system_into_qt_host")(
                source_value,
                window=window,
                webview=webview,
                current_state=current_state,
                loaded_label=source_value,
                status_message=f"Loaded source: {source_value}",
            )
            _get_helper("_record_recent_source")(
                current_state,
                kind="source",
                value=source_value,
                loaded_label=source_value,
            )
            _refresh_recent_menu()
        except Exception as exc:
            _get_helper("_show_host_error")(window, QMessageBox, "Load Source Failed", f"Could not load source: {exc}")

    load_source_action.triggered.connect(_load_source)
    file_menu.addAction(load_source_action)

    restore_last_action = QAction("Restore Last Source", window)
    _get_helper("_set_action_shortcut")(restore_last_action, "Ctrl+R")

    def _restore_last():
        try:
            _get_helper("_restore_last_source")(
                window=window,
                webview=webview,
                QUrl=QUrl,
                html_path=html_path,
                current_title=current_title,
                current_state=current_state,
            )
            _refresh_recent_menu()
        except Exception as exc:
            _get_helper("_show_host_error")(window, QMessageBox, "Restore Last Source Failed", f"Could not restore last source: {exc}")

    restore_last_action.triggered.connect(_restore_last)
    file_menu.addAction(restore_last_action)

    close_action = QAction("Close", window)
    _get_helper("_set_action_shortcut")(close_action, "Ctrl+W")
    close_action.triggered.connect(lambda: (_get_helper("_persist_shell_state")(current_state, window=window), window.close()))
    file_menu.addAction(close_action)

    open_navigate_action = QAction("Open Navigate", window)
    _get_helper("_set_action_shortcut")(open_navigate_action, "Ctrl+1")
    open_navigate_action.triggered.connect(
        lambda: _get_helper("_send_viewer_message")(
            webview,
            {"op": "set_panel_mode", "panel": "navigate", "expanded": True},
        )
    )
    view_menu.addAction(open_navigate_action)

    open_workbench_action = QAction("Open Workbench", window)
    _get_helper("_set_action_shortcut")(open_workbench_action, "Ctrl+2")
    open_workbench_action.triggered.connect(
        lambda: _get_helper("_send_viewer_message")(
            webview,
            {"op": "set_panel_mode", "panel": "workbench", "expanded": True},
        )
    )
    view_menu.addAction(open_workbench_action)

    close_panel_action = QAction("Close Panel Mode", window)
    _get_helper("_set_action_shortcut")(close_panel_action, "Escape")
    close_panel_action.triggered.connect(
        lambda: _get_helper("_send_viewer_message")(
            webview,
            {"op": "set_panel_mode", "panel": None, "expanded": False},
        )
    )
    view_menu.addAction(close_panel_action)

    export_html_action = QAction("Export HTML", window)
    _get_helper("_set_action_shortcut")(export_html_action, "Ctrl+Shift+S")

    def _export_html():
        if not hasattr(QFileDialog, "getSaveFileName"):
            _get_helper("_show_status")(window, "Export HTML is not available in the current Qt runtime.")
            return
        selected, _filter = QFileDialog.getSaveFileName(
            window,
            "Export MolSysViewer HTML",
            str(Path(html_path).with_name("molsysviewer-export.html")),
            "HTML files (*.html);;All files (*)",
        )
        if not selected:
            return
        try:
            destination = Path(selected).expanduser().resolve()
            _get_helper("_rebuild_qt_html")(
                current_state.get("molecular_system"),
                html_path=str(destination),
                title=current_title,
            )
            _get_helper("_show_status")(window, f"Exported HTML: {destination.name}")
        except Exception as exc:
            _get_helper("_show_host_error")(window, QMessageBox, "Export HTML Failed", f"Could not export HTML: {exc}")

    export_html_action.triggered.connect(_export_html)
    export_menu.addAction(export_html_action)

    export_figure_action = QAction("Export Figure", window)
    _get_helper("_set_action_shortcut")(export_figure_action, "Ctrl+Shift+E")

    def _export_figure():
        if current_state.get("molecular_system") is None:
            _get_helper("_show_status")(window, "No molecular system is loaded for figure export.")
            return
        if not hasattr(QFileDialog, "getSaveFileName"):
            _get_helper("_show_status")(window, "Export Figure is not available in the current Qt runtime.")
            return
        selected, _filter = QFileDialog.getSaveFileName(
            window,
            "Export MolSysViewer figure",
            str(Path(html_path).with_name("molsysviewer-figure.png")),
            "PNG files (*.png);;All files (*)",
        )
        if not selected:
            return
        try:
            destination = Path(selected).expanduser().resolve()
            _get_helper("_export_qt_figure")(
                current_state["molecular_system"],
                output_filename=str(destination),
                title=current_title,
            )
            _get_helper("_show_status")(window, f"Exported Figure: {destination.name}")
        except Exception as exc:
            _get_helper("_show_host_error")(window, QMessageBox, "Export Figure Failed", f"Could not export figure: {exc}")

    export_figure_action.triggered.connect(_export_figure)
    export_menu.addAction(export_figure_action)

    about_action = QAction("About MolSysViewer Qt Prototype", window)

    def _show_about() -> None:
        message = (
            "MolSysViewer Qt Prototype\n\n"
            "Thin standalone host for the shared MolSysViewer runtime.\n"
            "Current goal: validate the dedicated app shell before final packaging.\n\n"
            "Use File to load a demo, file, PDB ID, or MolSysMT source."
        )
        if hasattr(QMessageBox, "information"):
            QMessageBox.information(window, "About MolSysViewer Qt Prototype", message)
        else:
            _get_helper("_show_status")(window, "About: MolSysViewer Qt Prototype")

    about_action.triggered.connect(_show_about)
    help_menu.addAction(about_action)

    current_source_action = QAction("Show Current Source", window)

    def _show_current_source() -> None:
        _get_helper("_show_status")(window, f"Current source: {_get_helper('_current_source_summary')(current_state)}")

    current_source_action.triggered.connect(_show_current_source)
    help_menu.addAction(current_source_action)

    host_info_action = QAction("Show Host Info", window)

    def _show_host_info() -> None:
        message = _get_helper("_host_info_message")(current_state, html_path)
        if hasattr(QMessageBox, "information"):
            QMessageBox.information(window, "MolSysViewer Qt Host Info", message)
        else:
            _get_helper("_show_status")(window, "Host info is available.")

    host_info_action.triggered.connect(_show_host_info)
    help_menu.addAction(host_info_action)

    reload_last_action = QAction("Reload Last Source", window)

    def _reload_last_source() -> None:
        _get_helper("_restore_last_source")(
            window=window,
            webview=webview,
            QUrl=QUrl,
            html_path=html_path,
            current_title=current_title,
            current_state=current_state,
        )
        _refresh_recent_menu()

    reload_last_action.triggered.connect(_reload_last_source)
    help_menu.addAction(reload_last_action)
