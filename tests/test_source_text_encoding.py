"""Repository-source guards must not depend on the native text encoding."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "relative",
    [
        "tests/loaders/test_load_from_molsysmt.py",
        "tests/test_e2e_reliability.py",
        "tests/test_reporting_protocol.py",
    ],
)
def test_source_guard_readers_declare_utf8(relative):
    tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
    readers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "read_text"
    ]
    assert readers, relative
    for node in readers:
        encoding = next((keyword.value for keyword in node.keywords if keyword.arg == "encoding"), None)
        assert isinstance(encoding, ast.Constant) and encoding.value == "utf-8", f"{relative}:{node.lineno}"
