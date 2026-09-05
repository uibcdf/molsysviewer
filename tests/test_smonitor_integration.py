import ast
from pathlib import Path

from molsysviewer._private.exceptions import ArgumentError
from molsysviewer import MolSysView
from molsysviewer.demo import demo
from molsysviewer.new_view import new_view
from molsysviewer._private.smonitor import CATALOG, PACKAGE_ROOT, META
from smonitor import get_manager
from smonitor.integrations import emit_from_catalog


def test_smonitor_catalog_emit():
    event = emit_from_catalog(
        CATALOG["viewer_init_failed"],
        package_root=PACKAGE_ROOT,
        meta=META,
        extra={"reason": "test", "message": "failed"},
    )
    assert event.get("code") == "MOLSYSVIEWER-VIEWER-INIT-FAILED"


def test_argument_error_message():
    exc = ArgumentError("selection", value="bad", caller="molsysviewer.test")
    assert str(exc)


def test_public_wrappers_emit_signal_timeline_entries(tmp_path):
    manager = get_manager()
    previous_profiling = manager.config.profiling
    previous_sample = manager.config.profiling_sample_rate
    previous_buffer = manager.config.profiling_buffer_size
    manager._timeline.clear()
    manager._timings.clear()
    manager.configure(profiling=True, profiling_sample_rate=1.0, profiling_buffer_size=16384)

    try:
        view = demo["dialanine"]
        view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
        manager._timeline.clear()
        manager._timings.clear()

        scripted_view = MolSysView(debug_js=True)
        scripted_view.widget.send = lambda _msg: None  # type: ignore[attr-defined]
        scripted_view._request_image_export = lambda **_kwargs: {  # type: ignore[attr-defined]  # noqa: SLF001
            "event": "image_export",
            "format": "png",
            "data_uri": "data:image/png;base64,iVBORw0KGgo=",
        }

        new_view(
            view._molsys,  # noqa: SLF001
            view=scripted_view,
            load_mode="selection",
            skip_digestion=True,
        )

        region = view.regions.add(atom_indices=[0, 1, 2], tag="frag", representation="sticks", skip_digestion=True)
        region.hide(skip_digestion=True)
        view.whole.hide(skip_digestion=True)
        view.shapes.clear(skip_digestion=True)
        view.reset_camera(skip_digestion=True)
        view.get_camera_snapshot(skip_digestion=True)
        view.set_camera_snapshot({"target": [0, 0, 0]}, skip_digestion=True)
        view.set_panel_mode("addons", skip_digestion=True)
        view.set_workspace("core", skip_digestion=True)
        view.set_workspace_panel("addons", workspace="core", skip_digestion=True)
        view.workspace_catalog(skip_digestion=True)
        view.workspace_panels("core", skip_digestion=True)
        view.workspace_sections("core", skip_digestion=True)
        view.workspace_runtime(skip_digestion=True)
        view.workspace_runtime(pretty=True, skip_digestion=True)
        view.get_panel_mode_state(pretty=True)
        view.export.html(str(tmp_path / "smonitor.html"), include_popout=False, skip_digestion=True)
        scripted_view.export.image(str(tmp_path / "smonitor.png"), transparent=True, preset="current", skip_digestion=True)
        scripted_view.export.figure_publication_set(
            str(tmp_path / "pub-set"),
            include_current=True,
            skip_digestion=True,
        )

        timeline = manager.report()["timeline"]
        keys = [entry["key"] for entry in timeline]
        tags_by_key = {entry["key"]: set(entry.get("tags", [])) for entry in timeline}
        meta_by_key = {entry["key"]: entry.get("meta", {}) for entry in timeline}

        assert "molsysviewer.regions.hide" in keys
        assert "molsysviewer.whole.hide" in keys
        assert "molsysviewer.shapes.clear" in keys
        assert "molsysviewer.viewer.reset_camera" in keys
        assert "molsysviewer.viewer.get_camera_snapshot" in keys
        assert "molsysviewer.viewer.set_camera_snapshot" in keys
        assert "molsysviewer.viewer.set_panel_mode" in keys
        assert "molsysviewer.viewer.set_workspace" in keys
        assert "molsysviewer.viewer.set_workspace_panel" in keys
        assert "molsysviewer.viewer.workspace_catalog" in keys
        assert "molsysviewer.viewer.workspace_panels" in keys
        assert "molsysviewer.viewer.workspace_sections" in keys
        assert "molsysviewer.viewer.workspace_runtime" in keys
        assert "molsysviewer.viewer.get_panel_mode_state" in keys
        assert "molsysviewer.new_view.new_view" in keys
        assert "molsysviewer.exports.html" in keys
        assert "molsysviewer.exports.image" in keys
        assert "molsysviewer.exports.figure_publication_set" in keys
        assert "molsysviewer.exports.figure_variants" in keys
        assert "molsysviewer.exports.figure" in keys

        assert "region" in tags_by_key["molsysviewer.regions.hide"]
        assert "whole" in tags_by_key["molsysviewer.whole.hide"]
        assert "shape" in tags_by_key["molsysviewer.shapes.clear"]
        assert "camera" in tags_by_key["molsysviewer.viewer.reset_camera"]
        assert "panel" in tags_by_key["molsysviewer.viewer.set_panel_mode"]
        assert "factory" in tags_by_key["molsysviewer.new_view.new_view"]
        assert "export" in tags_by_key["molsysviewer.exports.html"]
        assert "image" in tags_by_key["molsysviewer.exports.image"]
        assert "figure" in tags_by_key["molsysviewer.exports.figure_publication_set"]
        assert meta_by_key["molsysviewer.viewer.get_camera_snapshot"].get("pretty") is None
        assert meta_by_key["molsysviewer.viewer.set_camera_snapshot"].get("snapshot_keys") == ["target"]
        assert meta_by_key["molsysviewer.viewer.set_panel_mode"].get("panel") == "addons"
        assert meta_by_key["molsysviewer.viewer.set_panel_mode"].get("expanded") is True
        assert meta_by_key["molsysviewer.viewer.set_workspace"].get("workspace") == "core"
        assert meta_by_key["molsysviewer.viewer.set_workspace_panel"].get("panel") == "addons"
        assert meta_by_key["molsysviewer.viewer.set_workspace_panel"].get("workspace") == "core"
        assert meta_by_key["molsysviewer.viewer.workspace_catalog"].get("current_workspace") == "core"
        assert meta_by_key["molsysviewer.viewer.workspace_catalog"].get("workspace_count") >= 1
        assert meta_by_key["molsysviewer.viewer.workspace_panels"].get("workspace") == "core"
        assert meta_by_key["molsysviewer.viewer.workspace_sections"].get("workspace") == "core"
        assert meta_by_key["molsysviewer.viewer.workspace_runtime"].get("current_workspace") == "core"
        assert meta_by_key["molsysviewer.viewer.workspace_runtime"].get("panel_count") == 2
        assert meta_by_key["molsysviewer.viewer.workspace_runtime"].get("pretty") is True
        assert meta_by_key["molsysviewer.viewer.get_panel_mode_state"].get("pretty") is True
        assert meta_by_key["molsysviewer.new_view.new_view"].get("load_mode") == "selection"
        assert meta_by_key["molsysviewer.new_view.new_view"].get("syntax") == "MolSysMT"
        assert meta_by_key["molsysviewer.new_view.new_view"].get("reused_view") is True
        assert meta_by_key["molsysviewer.new_view.new_view"].get("molecular_system_form") == "molsysmt.MolSys"
        assert meta_by_key["molsysviewer.exports.html"].get("include_popout") is False
        assert meta_by_key["molsysviewer.exports.image"].get("transparent") is True
        assert meta_by_key["molsysviewer.exports.image"].get("preset") == "current"
        assert meta_by_key["molsysviewer.exports.figure_publication_set"].get("include_current") is True
        assert meta_by_key["molsysviewer.exports.figure_publication_set"].get("has_figure_spec") is False
        assert meta_by_key["molsysviewer.exports.figure_variants"].get("variant_count") == 4
        assert meta_by_key["molsysviewer.exports.figure"].get("has_figure_spec") is True
    finally:
        manager.configure(
            profiling=previous_profiling,
            profiling_sample_rate=previous_sample,
            profiling_buffer_size=previous_buffer,
        )


def test_public_digest_entrypoints_have_signal_decorators():
    targets = [
        Path("molsysviewer/viewer/core.py"),
        Path("molsysviewer/new_view.py"),
        Path("molsysviewer/whole.py"),
        Path("molsysviewer/regions.py"),
        Path("molsysviewer/layers.py"),
        Path("molsysviewer/config/__init__.py"),
    ]
    targets.extend(sorted(Path("molsysviewer/shapes").glob("*.py")))

    missing: list[str] = []

    for path in targets:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                decorators = [ast.unparse(deco) for deco in node.decorator_list]
                if any("digest" in deco for deco in decorators) and not any("signal" in deco for deco in decorators):
                    missing.append(f"{path}:{node.name}")
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if not isinstance(item, ast.FunctionDef):
                        continue
                    decorators = [ast.unparse(deco) for deco in item.decorator_list]
                    if any("digest" in deco for deco in decorators) and not any("signal" in deco for deco in decorators):
                        missing.append(f"{path}:{node.name}.{item.name}")

    assert missing == []


# --- the catalog's message templates must actually reach SMonitor ------------------
#
# Until 2026-09-01 none of them did. `CODES` was keyed by catalog key and held plain
# strings; SMonitor looks a template up by *code* and reads a per-profile field off a
# *dict*, so every lookup missed and `message_from_catalog` fell back to the
# `default_message` its caller passes. Nothing looked broken because every caller passes
# one, which is exactly why this needs a test rather than a reader.

def test_every_catalog_entry_has_a_template_smonitor_can_resolve():
    """Keyed by code, valued by a per-profile dict, with a message for every profile.

    Mutation: key `CODES` by the catalog key again, or give an entry a plain string,
    and this fails.
    """
    from molsysviewer._private.smonitor.catalog import CATALOG, CODES, MESSAGES, PROFILES_FIELDS

    for key, template in MESSAGES.items():
        code = CATALOG[key]["code"]
        assert code in CODES, f"{key}: no template reachable under its code {code!r}"
        entry = CODES[code]
        assert isinstance(entry, dict), f"{code}: template must be a dict, not {type(entry).__name__}"
        for field in PROFILES_FIELDS:
            assert entry.get(field) == template, f"{code}: {field} does not carry the template"


def test_a_catalog_message_renders_its_template_rather_than_the_fallback():
    """The fallback is what hid the defect, so the test must be able to see past it.

    A `default_message` that could never be mistaken for the template is the only way
    to tell "the template rendered" from "the caller's default was returned".
    """
    from molsysviewer._private.smonitor_emit import message_from_catalog

    message = message_from_catalog(
        "argument_error",
        extra={"argument": "selection", "value": 3, "caller": "molsysviewer.viewer.get"},
        default_message="THIS FALLBACK MUST NOT BE WHAT COMES BACK",
    )
    assert "THIS FALLBACK" not in message
    assert "selection" in message and "molsysviewer.viewer.get" in message


def test_a_rendered_catalog_message_leaves_no_unfilled_placeholder():
    """A placeholder nobody fills renders literally, as `{file}` did for years.

    SMonitor leaves an unknown placeholder untouched rather than raising, so a template
    that names a field its caller does not pass is invisible until a user reads the
    message. `file_already_handled` asked for `{file}` while its only caller passed
    `filename`; nobody saw it because no template rendered at all.

    **What this cannot cover, and why.** The scale-budget warning authors its sentence
    twice -- once as the catalog template, once as a hardcoded f-string handed to
    `warnings.warn` -- so the text a user reads there does not come through the catalog
    and a mutation of its structured fields cannot be seen from here. Guarding it needs
    that call site migrated to the diagnostic bundle's `warn()`, which emits and warns
    from one template. Until then, asserting on its Python warning would be a test that
    passes when the thing it names is removed.
    """
    import re

    from molsysviewer._private.exceptions import ArgumentError, FileAlreadyHandledError

    rendered = [
        str(FileAlreadyHandledError("system.pdb")),
        str(ArgumentError("selection", 3, caller="molsysviewer.viewer.get")),
    ]
    for message in rendered:
        assert message, "a catalog message came back empty"
        assert not re.search(r"\{\w+\}", message), f"unfilled placeholder in: {message}"

    assert "system.pdb" in rendered[0]
