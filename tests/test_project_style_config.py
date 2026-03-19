from __future__ import annotations

from pathlib import Path

from molsysviewer import MolSysView
from molsysviewer.config import load_project_config


def _write_project_config(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "from molsysviewer import Style",
                "",
                'DEFAULT_SCENE_STYLE = Style(preset="polymer-cartoon", name="Default Polymer")',
                "STYLES = {",
                '    "publication": Style(preset="polymer-cartoon", name="Publication"),',
                '    "atomic": Style(representation="ball-and-stick", name="Atomic"),',
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_load_project_config_reads_explicit_file(tmp_path):
    config_path = tmp_path / "_molsysviewer.py"
    _write_project_config(config_path)

    data = load_project_config(config_path)

    assert data["path"] == str(config_path)
    assert data["default_scene_style"].preset == "polymer-cartoon"
    assert sorted(data["styles"].keys()) == ["atomic", "publication"]


def test_styles_load_project_config_registers_styles_without_implicit_apply(tmp_path):
    config_path = tmp_path / "_molsysviewer.py"
    _write_project_config(config_path)
    view = MolSysView()

    summary = view.styles.load_project_config(str(config_path))

    assert summary["style_tags"] == ["atomic", "publication"]
    assert summary["applied_default"] is False
    assert view.styles.tags() == ["atomic", "publication"]
    assert view.styles.current() is None


def test_styles_load_project_config_can_apply_default_explicitly(tmp_path):
    config_path = tmp_path / "_molsysviewer.py"
    _write_project_config(config_path)
    view = MolSysView()

    summary = view.styles.load_project_config(str(config_path), apply_default=True)

    assert summary["applied_default"] is True
    assert view._message_history[-1]["op"] == "set_global_representation"  # noqa: SLF001
    assert view._message_history[-1]["preset"] == "polymer-cartoon"  # noqa: SLF001
    current = view.styles.current()
    assert current is not None
    assert current.preset == "polymer-cartoon"


def test_explicit_style_application_still_wins_after_loading_project_config(tmp_path):
    config_path = tmp_path / "_molsysviewer.py"
    _write_project_config(config_path)
    view = MolSysView()
    view.styles.load_project_config(str(config_path), apply_default=True)

    view.styles.apply(tag="atomic")

    current = view.styles.current()
    assert current is not None
    assert current.representation == "ball-and-stick"
