import pytest

pytest.importorskip("anywidget")
pytest.importorskip("traitlets")

from molsysviewer import demo
from molsysviewer.standalone import build_standalone0_html, launch_standalone0


def test_build_standalone0_html_writes_file(tmp_path):
    view = demo["dialanine"]
    outfile = tmp_path / "standalone0.html"

    result = build_standalone0_html(view, str(outfile), include_popout=False)

    assert result == str(outfile.resolve())
    assert outfile.exists()
    text = outfile.read_text(encoding="utf-8")
    assert "MolSysViewer Standalone 0" in text


def test_launch_standalone0_can_skip_browser(tmp_path):
    view = demo["dialanine"]
    outfile = tmp_path / "launch.html"

    result = launch_standalone0(view, str(outfile), open_browser=False, include_popout=False)

    assert result == str(outfile.resolve())
    assert outfile.exists()
