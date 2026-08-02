import ast
from pathlib import Path

from molsysviewer import MolSysView, demo
from molsysviewer.loaders import load_from_molsysmt
from molsysviewer.transport import LazyMolecularMessage


def test_load_from_molsysmt_creates_a_lazy_direct_molsys_projection(monkeypatch):
    source_view = demo["dialanine"]
    source = source_view.molsys
    original_to_form = type(source).to_form
    viewer_json_calls: list[str] = []

    def reject_viewer_json(self, target, *args, **kwargs):
        if target == "molsysmt.ViewerJSON":
            viewer_json_calls.append(target)
            raise AssertionError("ViewerJSON must not be used by the loader")
        return original_to_form(self, target, *args, **kwargs)

    monkeypatch.setattr(type(source), "to_form", reject_viewer_json)
    view = MolSysView()
    result = load_from_molsysmt(molecular_system=source, view=view)

    assert result is view
    message = next(msg for msg in view._test_message_log if msg.get("op") == "load_molsys_payload")  # noqa: SLF001
    assert isinstance(message, LazyMolecularMessage)
    assert not message.is_materialized
    assert viewer_json_calls == []

    payload = message["payload"]
    assert payload["atoms"]["atom_name"][:3] == ["H1", "CH3", "H2"]
    assert payload["structures"]
    assert viewer_json_calls == []


def test_load_from_molsysmt_creates_view_when_missing():
    source_view = demo["dialanine"]

    result = load_from_molsysmt(molecular_system=source_view.molsys)

    assert isinstance(result, MolSysView)
    assert any(msg.get("op") == "load_molsys_payload" for msg in result._test_message_log)  # noqa: SLF001


def test_product_python_never_requests_a_viewerjson_intermediate():
    package_root = Path(__file__).parents[2] / "molsysviewer"
    offenders: list[str] = []
    for path in package_root.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        if any(
            isinstance(node, ast.Constant)
            and node.value == "molsysmt.ViewerJSON"
            for node in ast.walk(tree)
        ):
            offenders.append(str(path.relative_to(package_root)))

    assert offenders == []
