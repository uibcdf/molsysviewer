"""Review public call shapes separately from argument-digestion coverage.

This is a component-local contract for the reviewed Viewer roots. It does not
infer scientific stability from an import or freeze private implementation names.
"""

from __future__ import annotations

import argparse
import dataclasses
import inspect
import json
import math
from collections import deque
from collections.abc import Mapping
from enum import Enum
from pathlib import Path

import numpy as np
from public_api_inventory import MAX_DEPTH, _owned_by_molsysviewer, _public_names, public_roots

BASELINE = Path(__file__).with_name("public_api_contract_baseline.json")
RULES = Path(__file__).with_name("public_api_stability.json")


def encode_default(value):
    """Encode supported defaults without addresses or lossy string coercion."""
    if value is dataclasses._HAS_DEFAULT_FACTORY:
        return {"kind": "default_factory"}
    if value is inspect.Parameter.empty:
        return {"kind": "required"}
    if value is None or type(value) in {str, bool, int}:
        return {"kind": "literal", "type": type(value).__name__, "value": value}
    if isinstance(value, np.generic):
        return {"kind": "numpy_scalar", "dtype": str(value.dtype), "value": encode_default(value.item())}
    if isinstance(value, float):
        return {"kind": "float", "value": value if math.isfinite(value) else str(value), "binary64": value.hex()}
    if isinstance(value, Enum):
        return {"kind": "enum", "type": type(value).__module__ + "." + type(value).__qualname__, "name": value.name}
    if isinstance(value, type):
        return {"kind": "type", "name": value.__module__ + "." + value.__qualname__}
    if isinstance(value, (tuple, list)):
        return {"kind": type(value).__name__, "items": [encode_default(item) for item in value]}
    if isinstance(value, Mapping):
        return {"kind": "mapping", "items": [[encode_default(k), encode_default(v)] for k, v in value.items()]}
    if isinstance(value, np.ndarray):
        if value.size > 4096:
            raise TypeError("Review oversized array defaults explicitly.")
        return {
            "kind": "array",
            "dtype": str(value.dtype),
            "shape": list(value.shape),
            "values": encode_default(value.tolist()),
        }
    raise TypeError(f"Review a deterministic default encoding for {type(value).__module__}.{type(value).__qualname__}.")


def call_shape(function):
    """Record call binding, not implementation/annotation spelling."""
    try:
        signature = inspect.signature(function)
    except ValueError:
        # Some exported string/container subclasses inherit a C constructor.
        # Name its actual builtin owner explicitly; never invent a signature.
        if isinstance(function, type) and "__signature__" not in function.__dict__:
            for base in function.__mro__[1:]:
                if (
                    base.__module__ == "builtins"
                    and function.__new__ is base.__new__
                    and function.__init__ is base.__init__
                ):
                    return {
                        "constructor": {"kind": "inherited_builtin", "base": base.__module__ + "." + base.__qualname__},
                        "async": False,
                    }
        raise
    return {
        "parameters": [
            {"name": p.name, "kind": p.kind.name, "default": encode_default(p.default)}
            for p in signature.parameters.values()
        ],
        "async": inspect.iscoroutinefunction(inspect.unwrap(function)),
    }


def classification(path, module, rules):
    """Use reviewed route/module rules, never a blanket stability promotion."""
    matches = [
        rule
        for rule in rules
        if (
            path == rule.get("route")
            or path.startswith(rule.get("route", "\0") + ".")
            or module == rule.get("module")
            or module.startswith(rule.get("module", "\0") + ".")
        )
    ]
    if not matches:
        raise ValueError(f"No reviewed stability rule for {path} ({module}).")
    priority = max(rule["priority"] for rule in matches)
    selected = [rule for rule in matches if rule["priority"] == priority]
    if len({(rule["stability"], rule["reason"]) for rule in selected}) != 1:
        raise ValueError(f"Ambiguous stability rules for {path}.")
    return {key: selected[0][key] for key in ("stability", "reason")}


def build_contract(rules=None):
    """Snapshot the same real manager/handle roots as the digestion inventory."""
    if rules is None:
        rules = json.loads(RULES.read_text())["rules"]
    declarations, seen = {}, set()
    with public_roots() as roots:
        queue = deque((path, owner, 0) for path, owner in roots.items())
        while queue:
            path, owner, depth = queue.popleft()
            if id(owner) in seen or depth > MAX_DEPTH:
                continue
            seen.add(id(owner))
            for name in _public_names(owner):
                route = path + "." + name
                static = inspect.getattr_static(owner, name, None)
                if isinstance(owner, type) and not (
                    inspect.isfunction(static)
                    or isinstance(static, (classmethod, staticmethod))
                    or _owned_by_molsysviewer(static)
                    or (isinstance(static, property) and _owned_by_molsysviewer(static.fget))
                ):
                    continue
                if isinstance(static, property) and _owned_by_molsysviewer(static.fget):
                    declarations[route] = {
                        "kind": "property",
                        "readable": static.fget is not None,
                        "writable": static.fset is not None,
                        **classification(route, static.fget.__module__, rules),
                    }
                try:
                    value = getattr(owner, name)
                except Exception:
                    # State-dependent properties retain their static declaration.
                    continue
                if not _owned_by_molsysviewer(value):
                    continue
                if callable(value) and not isinstance(value, type):
                    if isinstance(owner, type) and not (
                        inspect.isfunction(static)
                        or isinstance(static, (classmethod, staticmethod))
                        or _owned_by_molsysviewer(static)
                    ):
                        continue
                    declarations[route] = {
                        "kind": "callable",
                        **call_shape(value),
                        **classification(route, value.__module__, rules),
                    }
                else:
                    if isinstance(value, type):
                        declarations[route] = {
                            "kind": "class",
                            **call_shape(value),
                            **classification(route, value.__module__, rules),
                        }
                    queue.append((route, value, depth + 1))
    return {"schema": "molsysviewer.public_api_contract@1", "declarations": dict(sorted(declarations.items()))}


def _compatible_parameter_extension(params, revised):
    """Prove unchanged old bindings for optional insertions, not full semantics."""
    old = {parameter["name"]: parameter for parameter in params}
    new = {parameter["name"]: parameter for parameter in revised}
    if any(new.get(name) != parameter for name, parameter in old.items()):
        return False
    extra = [parameter for parameter in revised if parameter["name"] not in old]
    positional = {"POSITIONAL_ONLY", "POSITIONAL_OR_KEYWORD"}
    if any(
        parameter["default"]["kind"] == "required" or parameter["kind"] not in positional | {"KEYWORD_ONLY"}
        for parameter in extra
    ):
        return False
    old_positional = [parameter["name"] for parameter in params if parameter["kind"] in positional]
    new_positional = [parameter["name"] for parameter in revised if parameter["kind"] in positional]
    if new_positional[: len(old_positional)] != old_positional:
        return False
    # A new positional parameter before *args would consume an old variadic
    # argument even though Signature.bind still accepts the call.
    if any(parameter["kind"] == "VAR_POSITIONAL" for parameter in params) and len(new_positional) != len(
        old_positional
    ):
        return False
    return True


def compare_contracts(before, after):
    """Describe reviewed changes; compatibility is call-shape-only, not science."""
    old, new = before["declarations"], after["declarations"]
    changes = []
    for route in sorted(old.keys() | new.keys()):
        if route not in old:
            changes.append({"route": route, "change": "added", "compatibility": "addition"})
        elif route not in new:
            changes.append({"route": route, "change": "removed", "compatibility": "breaking"})
        elif old[route] != new[route]:
            a, b = old[route], new[route]
            compatible = (
                a.get("kind") == b.get("kind")
                and a.get("kind") in {"callable", "class"}
                and a.get("async") == b.get("async")
            )
            headers_a = {key: value for key, value in a.items() if key not in {"parameters", "stability", "reason"}}
            headers_b = {key: value for key, value in b.items() if key not in {"parameters", "stability", "reason"}}
            compatible = compatible and headers_a == headers_b
            params = a.get("parameters", [])
            revised = b.get("parameters", [])
            compatible = compatible and _compatible_parameter_extension(params, revised)
            classification_changed = (a["stability"], a["reason"]) != (b["stability"], b["reason"])
            shape_a = {key: value for key, value in a.items() if key not in {"stability", "reason"}}
            shape_b = {key: value for key, value in b.items() if key not in {"stability", "reason"}}
            if shape_a == shape_b and classification_changed:
                compatibility = "classification_review"
            else:
                compatibility = (
                    ("compatible_extension" if len(revised) > len(params) else "compatible_reordering")
                    if compatible
                    else "breaking"
                )
            changes.append(
                {
                    "route": route,
                    "change": "changed",
                    "compatibility": compatibility,
                    **({"classification_changed": True} if classification_changed else {}),
                }
            )
    return changes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-baseline", action="store_true", help="Write reviewed declarations; generation itself is not approval."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    current = build_contract()
    if args.write_baseline:
        BASELINE.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        print(f"Wrote {len(current['declarations'])} declarations for explicit review.")
        return 0
    if args.json:
        print(json.dumps(current, indent=2, sort_keys=True))
        return 0
    changes = compare_contracts(json.loads(BASELINE.read_text()), current)
    print(json.dumps({"declarations": len(current["declarations"]), "changes": changes}, indent=2))
    return int(bool(changes))


if __name__ == "__main__":
    raise SystemExit(main())
