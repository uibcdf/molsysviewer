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
        # Forwarded as given, so the runtime selection is resolved by the
        # implementation and never quietly defaulted in the public wrapper.
        "runtime": None,
        "runtime_assets_dir": None,
    }
