"""Guards for the Python↔JS boundary.

Four separate defects during dogfooding shared one shape: a public argument that
Python accepts and validates, and that something downstream then ignores in
silence — an argument with no digester, an op no handler reads, a value the
frontend does not know.

These sweeps are cheap and deterministic, and would have caught every one of
them. See `devguide/python_js_boundary_audit_2026_07.md`.
"""

from __future__ import annotations

import ast
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1] / "molsysviewer"
ARGUMENT_DIR = ROOT / "_private" / "arg_digestion" / "argument"
JS_SRC = ROOT / "js" / "src"

NOT_ARGUMENTS = {"self", "cls", "skip_digestion"}


def _has_digest_decorator(node: ast.AST) -> bool:
    for decorator in node.decorator_list:  # type: ignore[attr-defined]
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if (getattr(target, "attr", None) or getattr(target, "id", None)) == "digest":
            return True
    return False


def _python_sources():
    for path in ROOT.rglob("*.py"):
        if "_private/arg_digestion" in path.as_posix() or "/js/" in path.as_posix():
            continue
        yield path


def test_every_digested_argument_has_a_digester():
    """A `@digest()` argument with no digester emits DigestNotDigestedWarning.

    The public contract then goes unvalidated: this is how `value_range`,
    `replace` and `scheme` shipped without validation.
    """
    available = {p.stem for p in ARGUMENT_DIR.glob("*.py") if p.stem != "__init__"}

    missing: dict[str, str] = {}
    for path in _python_sources():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - not expected in-tree
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not _has_digest_decorator(node):
                continue
            args = node.args
            for arg in args.posonlyargs + args.args + args.kwonlyargs:
                name = arg.arg
                if name in NOT_ARGUMENTS or name.startswith("_"):
                    continue
                if name not in available:
                    missing.setdefault(name, f"{path.name}:{node.name}")

    assert not missing, (
        "public arguments declared under @digest() with no digester "
        f"(each emits DigestNotDigestedWarning): {missing}"
    )


def test_every_op_python_emits_is_handled_somewhere():
    """An op no handler reads is silently discarded.

    Handlers take several forms (`case "x"`, `op === "x"`), live in more than one
    file, and some are in the JS embedded in `widget.py` — all of them count.
    """
    emitted: dict[str, str] = {}
    for path in _python_sources():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r'["\']op["\']\s*:\s*["\']([a-z0-9_]+)["\']', text):
            emitted.setdefault(match.group(1), path.name)

    handled: set[str] = set()
    frontend = list(JS_SRC.rglob("*.ts")) + [ROOT / "widget.py"]
    for path in frontend:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        handled |= set(re.findall(r'case\s+["\']([a-z0-9_]+)["\']', text))
        handled |= set(re.findall(r'op\s*(?:===|!==)\s*["\']([a-z0-9_]+)["\']', text))

    orphans = {op: where for op, where in emitted.items() if op not in handled}
    assert not orphans, (
        f"ops emitted by Python that no frontend handler reads: {orphans}"
    )
