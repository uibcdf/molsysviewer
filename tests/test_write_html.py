import warnings

import pytest

pytest.importorskip("anywidget")
pytest.importorskip("traitlets")

from molsysviewer import MolSysView


def test_export_html_namespace_delegates(monkeypatch, tmp_path):
    view = MolSysView(debug_js=True)
    called = {}

    def fake_impl(output_filename, **kwargs):
        called["output_filename"] = output_filename
        called["kwargs"] = kwargs

    monkeypatch.setattr(view, "_write_html_impl", fake_impl)

    outfile = tmp_path / "out.html"
    view.export.html(str(outfile), title="TestTitle", include_controls=False, include_popout=False, mode="lite")

    assert called["output_filename"] == str(outfile)
    assert called["kwargs"] == {
        "title": "TestTitle",
        "include_controls": False,
        "include_popout": False,
        "mode": "lite",
        "inline_messages": True,
    }


def test_write_html_warns_and_delegates(monkeypatch, tmp_path):
    view = MolSysView(debug_js=True)
    called = {}

    def fake_impl(output_filename, **kwargs):
        called["output_filename"] = output_filename
        called["kwargs"] = kwargs

    monkeypatch.setattr(view, "_write_html_impl", fake_impl)

    outfile = tmp_path / "deprecated.html"
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        view.write_html(str(outfile), title="Old API")

    assert called["output_filename"] == str(outfile)
    assert called["kwargs"]["title"] == "Old API"
    assert any(isinstance(record.message, DeprecationWarning) for record in records)
