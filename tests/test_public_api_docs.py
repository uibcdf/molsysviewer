from __future__ import annotations

import inspect
import re
from pathlib import Path

from molsysviewer.demo import demo
from molsysviewer.regions import Region
from molsysviewer.selections import Selection


PUBLIC_API_DOC = (
    Path(__file__).parents[1] / "docs" / "content" / "developer" / "public_api.md"
)
DECLARATION_PATTERN = re.compile(
    r"`(?P<symbol>view(?:\.[A-Za-z_][A-Za-z0-9_]*)+)"
    r"(?P<call>\(\))?` \((?P<kind>method|property)\)"
)
VIEW_SYMBOL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])view(?:\.[A-Za-z_][A-Za-z0-9_]*|\[tag\])+"
)
PUBLIC_VIEW_API_START = "`MolSysView` is also explicitly growing"
PUBLIC_VIEW_API_END = "## Internal Python APIs"


def _declared_symbols() -> list[tuple[str, str]]:
    declarations = []
    for match in DECLARATION_PATTERN.finditer(PUBLIC_API_DOC.read_text(encoding="utf-8")):
        symbol = match.group("symbol")
        kind = match.group("kind")
        if kind == "method":
            assert match.group("call") == "()", f"Document callable {symbol} with ()"
        else:
            assert match.group("call") is None, f"Document property {symbol} without ()"
        declarations.append((symbol, kind))
    assert declarations, "public_api.md has no machine-checkable API kind declarations"
    return declarations


def _resolve_parent(view, symbol: str):
    parts = symbol.split(".")
    assert parts[0] == "view"
    parent = view
    for part in parts[1:-1]:
        parent = getattr(parent, part)
    return parent, parts[-1]


def _documented_view_symbols() -> list[str]:
    text = PUBLIC_API_DOC.read_text(encoding="utf-8")
    public_surface = text.split(PUBLIC_VIEW_API_START, maxsplit=1)[1]
    public_surface = public_surface.split(PUBLIC_VIEW_API_END, maxsplit=1)[0]
    symbols = sorted(set(VIEW_SYMBOL_PATTERN.findall(public_surface)))
    assert symbols, "public_api.md has no documented view.* symbols"
    return symbols


def _assert_symbol_exists(view, symbol: str) -> None:
    region_prefix = "view.regions[tag]"
    selection_prefix = "view.selections[tag]"
    if symbol.startswith(region_prefix):
        current = Region(view, "doc-region", "all", atom_indices=[])
        suffix = symbol[len(region_prefix) :]
    elif symbol.startswith(selection_prefix):
        current = Selection(view, "doc-selection")
        suffix = symbol[len(selection_prefix) :]
    else:
        current = view
        suffix = symbol[len("view") :]

    attributes = [part for part in suffix.split(".") if part]
    for attribute in attributes[:-1]:
        current = getattr(current, attribute)
    if attributes:
        getattr(current, attributes[-1])


def test_public_api_doc_declares_existing_methods_and_properties():
    view = demo["dialanine"]

    for symbol, declared_kind in _declared_symbols():
        parent, attribute = _resolve_parent(view, symbol)
        descriptor = inspect.getattr_static(type(parent), attribute)
        actual_kind = "property" if isinstance(descriptor, property) else "method"
        if actual_kind == "method":
            assert callable(getattr(parent, attribute)), f"{symbol} is not callable"
        assert actual_kind == declared_kind, (
            f"{symbol} is documented as {declared_kind}, but is a {actual_kind}"
        )


def test_public_api_doc_never_names_a_symbol_that_does_not_exist():
    view = demo["dialanine"]

    for symbol in _documented_view_symbols():
        try:
            _assert_symbol_exists(view, symbol)
        except AttributeError as error:
            raise AssertionError(f"public_api.md documents missing symbol {symbol}") from error
