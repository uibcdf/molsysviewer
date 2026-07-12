#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


CHAIN_PATTERN = re.compile(r"\b(?:view|viewer)(?:\.[A-Za-z_]\w*)+")
FENCE_PATTERN = re.compile(r"^```([^\n]*)\n(.*?)^```\s*$", re.DOTALL | re.MULTILINE)
HISTORICAL_SNAPSHOTS = {
    "architecture_snapshot_2025_11.md",
    "architecture_snapshot_2026_01.md",
}


def _python_sources(path: Path) -> Iterable[tuple[str, int]]:
    if path.suffix == ".py":
        yield path.read_text(encoding="utf-8"), 1
        return
    if path.suffix == ".ipynb":
        notebook = json.loads(path.read_text(encoding="utf-8"))
        for cell_index, cell in enumerate(notebook.get("cells", []), start=1):
            if cell.get("cell_type") == "code":
                yield "".join(cell.get("source", [])), cell_index
        return
    if path.suffix == ".md":
        text = path.read_text(encoding="utf-8")
        for match in FENCE_PATTERN.finditer(text):
            language = match.group(1).strip().lower()
            if language not in {"", "python", "py"}:
                continue
            yield match.group(2), text.count("\n", 0, match.start(2)) + 1


def _chains(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {
            chain
            for chain in CHAIN_PATTERN.findall(source)
            if chain.split(".")[-1] not in {"js", "map"}
            and not any(part.startswith("_") for part in chain.split(".")[1:])
        }
    chains: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        parts = [node.attr]
        value = node.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name) and value.id in {"view", "viewer"}:
            chain = ".".join([value.id, *reversed(parts)])
            if not any(part.startswith("_") for part in chain.split(".")[1:]):
                chains.add(chain)
    return chains


def _resolves(root: Any, chain: str) -> bool:
    current = root
    for attribute in chain.split(".")[1:]:
        if current is None:
            # A loaded-system proxy is unavailable on an empty live view. Its
            # deeper API belongs to MolSysMT and is outside this resolver.
            return True
        try:
            current = getattr(current, attribute)
        except (AttributeError, RuntimeError):
            return False
    return True


def _files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if root.is_file():
            yield root
            continue
        for path in sorted(root.rglob("*")):
            if any(part in {"_build", ".ipynb_checkpoints"} for part in path.parts):
                continue
            if path.suffix in {".md", ".ipynb", ".py"} and path.name not in HISTORICAL_SNAPSHOTS:
                yield path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve documented view.* calls against the live MolSysView API.")
    parser.add_argument("roots", nargs="+", type=Path)
    args = parser.parse_args(argv)

    import molsysviewer
    from molsysviewer import MolSysView

    live_view = MolSysView()
    unresolved: list[tuple[Path, int, str]] = []
    for path in _files(args.roots):
        for source, location in _python_sources(path):
            for chain in sorted(_chains(source)):
                roots = (live_view, molsysviewer) if chain.startswith("viewer.") else (live_view,)
                if not any(_resolves(root, chain) for root in roots):
                    unresolved.append((path, location, chain))

    for path, location, chain in unresolved:
        print(f"{path}:{location}: unresolved API chain {chain}")
    if unresolved:
        print(f"{len(unresolved)} unresolved API chain(s).", file=sys.stderr)
        return 1
    print("API resolver: 0 unresolved chains.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
