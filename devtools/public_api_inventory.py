"""The closed inventory of public callables and the argument digesters they still need.

Gate 9 of the pre-1.0 plan asks for every public callable to carry `@digest`. The count
that motivated it — 286 decorated against 515 not — was taken over every non-underscore
name in the package, and that is not the same set as the supported public API. It counts
implementation methods that happen to lack a leading underscore and that no user can
reach, and it says nothing about the part that actually costs time.

This produces two things instead:

**A public surface defined by reachability, not by spelling.** A callable is public when a
user can reach it from `import molsysviewer` or from a `MolSysView` instance by attribute
access, never passing through an underscore name. That is mechanical, it is what a user
can actually type, and it is closed: the walk terminates, so the result is a set rather
than an estimate.

**The size of the remaining work in the unit the work is done in.** Decorating a function
is one line; declaring the arguments it introduces is the job. `STRICTNESS = "warn"` means
decorating a callable whose arguments are undeclared trades a silent hole for a warning on
every call, so the number that matters is *distinct argument names with no digester*, not
function count.

Run it:

    python devtools/public_api_inventory.py            # the report
    python devtools/public_api_inventory.py --json     # the machine-readable inventory

`tests/test_public_api_inventory.py` pins the result so the surface cannot grow
undigested without a visible, deliberate change.
"""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Iterator, NamedTuple

import molsysviewer
from molsysviewer.demo import demo


ROOT = Path(__file__).resolve().parents[1]
DIGESTER_DIRECTORY = ROOT / "molsysviewer" / "_private" / "argdigest" / "argument"
BASELINE_PATH = Path(__file__).resolve().parent / "public_api_inventory_baseline.json"

#: Arguments that are never a user's to declare: the digestion escape hatch and the
#: instance itself.
NOT_USER_ARGUMENTS = frozenset({"self", "cls", "skip_digestion"})

#: Public callables that must **not** carry `@digest`, and why.
#:
#: Gate 9's rule is that every public callable is digested. Reaching zero without this
#: list would mean either decorating things where the decorator does nothing, or leaving
#: the number permanently short of its target with no way to tell debt from design.
#:
#: A *pure variadic forwarder* takes `*args, **kwargs`, passes them straight to a callable
#: that is itself digested, and names none of them. Decorating it digests nothing and adds
#: a layer — `devguide/digestion_and_dependencies.md` says so explicitly. A context
#: manager is not a call whose arguments can be judged at all.
#:
#: A *named delegating forwarder* is the same case with the parameters written out: every
#: one of them belongs to the callee, and the callee digests them. `view.get`'s signature
#: **is** `msm.get`'s, minus the system, so decorating it means digesting the same call
#: twice with two copies of the same rules — and the copies had already drifted:
#: `group_index` returned `True` for one caller and `[True]` for another, and
#: `region.get` refused 77 of 118 attributes that `msm.get` answers.
#:
#: The test is checkable rather than a matter of taste: **compare the two signatures.** If
#: a parameter is not the callee's, the forwarder is not pure and the exemption does not
#: apply. See `uibcdf/molsysviewer#71`.
#:
#: Every entry needs a reason, and the reason has to survive being read by someone who
#: suspects it is an excuse.
DELIBERATELY_NOT_DIGESTED: dict[str, str] = {
    "molsysviewer.build_standalone0_html":
        "lazy import wrapper; the imported callable is the one with a signature",
    "molsysviewer.launch_standalone0":
        "lazy import wrapper; the imported callable is the one with a signature",
    "molsysviewer.create_standalone_qt0_window":
        "lazy import wrapper; the imported callable is the one with a signature",
    "molsysviewer.launch_standalone_qt0":
        "lazy import wrapper; the imported callable is the one with a signature",
    "view.whole.get":
        "named delegating forwarder to msm.get; the whole *is* the system",
    "view.whole.info":
        "named delegating forwarder to msm.info; the whole *is* the system",
    "view.whole.select":
        "named delegating forwarder to msm.select; the whole *is* the system",
    "view.regions[…].info":
        "named delegating forwarder to msm.info, masked to the region's atoms",
    "view.regions[…].select":
        "named delegating forwarder to msm.select, with the region's elements as mask",
    "view.regions[…].get":
        "named delegating forwarder to msm.get, scoped to the region's atoms",
    "view.whole.convert":
        "named delegating forwarder to msm.convert; the whole *is* the system",
    "view.regions[…].convert":
        "named delegating forwarder to msm.convert, scoped to the region's atoms",
    "view.annotations.add":
        "alias forwarding to add_annotation, which digests",
    "view.history.coalescing":
        "context manager, not a call with arguments to judge",
    "view.history.suspended":
        "context manager, not a call with arguments to judge",
    "view.attributed_to":
        "context manager, not a call with arguments to judge",

    # The colour primitives the `color` digester is built on. Decorating them makes the
    # digester call the function it is digesting: `normalize_color` -> `digest_color` ->
    # `normalize_color`. Measured by doing it. A function a digester delegates to cannot
    # itself be digested by that digester, and there is no third place to put the rule.
    "molsysviewer.normalize_color":
        "the primitive `digest_color` delegates to; decorating it is a cycle",
    "molsysviewer.normalize_colors":
        "the primitive `digest_color` delegates to; decorating it is a cycle",
    "molsysviewer.colors.normalize_color":
        "the primitive `digest_color` delegates to; decorating it is a cycle",
    "molsysviewer.colors.normalize_colors":
        "the primitive `digest_color` delegates to; decorating it is a cycle",

    # The `shapes` forwarders, and the measurement most likely to be misread as debt.
    #
    # Each takes `*args, **kwargs` and hands them to a sub-manager method that has a
    # closed keyword-only signature and its own `@digest`. Decorating the forwarder was
    # tried and measured: **nothing is digested and every call warns.** ArgDigest digests
    # `args` (the empty tuple, under the parameter's own name) and leaves the `**kwargs`
    # keys inside the mapping, so `tag`, `centers` and the rest never reach their
    # digesters — verified by instrumenting `digest_tag` and watching it never fire.
    #
    # This is why `args` shows up in the inventory as an argument name wanted by thirteen
    # callables. **Writing a `digest_args` would be the wrong fix**: it would silence a
    # warning that is correctly reporting that these functions should not be decorated.
    #
    # Two of them carried `@digest` already and had been emitting
    # `DigestNotDigestedWarning` on every real call. Nobody saw it because the only test
    # that reaches them passes `skip_digestion=True`.
    "view.shapes.add_anisotropy_ellipsoids":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.add_channel_tube":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.add_displacement_vectors":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.add_interaction_sites":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.add_links":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.add_pharmacophore_features":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.add_pocket_blob":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.add_pocket_surface":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.add_rings":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.add_scalar_isosurface":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.add_set_alpha_spheres":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.add_tetrahedra":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.add_triangle_faces":
        "pure forwarder to a digested sub-manager method; see the note above",
    "view.shapes.interaction_sites.add_pharmacophore_features":
        "pure forwarder to a digested sub-manager method; see the note above",
}

#: How deep the attribute walk goes. The public surface is a handful of managers hanging
#: off the view and off the package; anything deeper is reached through one of them.
MAX_DEPTH = 4


class PublicCallable(NamedTuple):
    path: str
    qualified_name: str
    module: str
    digested: bool
    arguments: tuple[str, ...]

    @property
    def caller(self) -> str:
        """The string ArgDigest builds for this callable: `<owner module>.<name>`.

        Recorded so the inventory can be checked against callers observed at runtime,
        which is the only way to know the walk reaches what users actually call.
        """

        return f"{self.module}.{self.path.rsplit('.', 1)[1]}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "qualified_name": self.qualified_name,
            "module": self.module,
            "caller": self.caller,
            "digested": self.digested,
            "arguments": list(self.arguments),
        }


def declared_digesters() -> set[str]:
    """The argument names that already have a digester.

    `DIGESTION_STYLE = "package"` means one module per argument name, so the file names
    are the inventory. Reading the directory rather than importing keeps this usable even
    while a digester is mid-edit.
    """

    return {
        path.stem
        for path in DIGESTER_DIRECTORY.glob("*.py")
        if not path.stem.startswith("_")
    }


def _is_digested(function: Any) -> bool:
    """`@digest` records its plan on the wrapper, and `functools.wraps` carries it out
    through `@signal` and `@dep_digest`."""

    return getattr(function, "digestion_plan", None) is not None


def _user_arguments(function: Any) -> tuple[str, ...]:
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return ()

    return tuple(
        name
        for name, parameter in signature.parameters.items()
        if name not in NOT_USER_ARGUMENTS
        # `*others` is bound as one tuple under that name and digested like any other, so
        # it needs a digester. `**kwargs` is not: ArgDigest digests each key by its own
        # name, never the mapping.
        and parameter.kind is not parameter.VAR_KEYWORD
    )


def _module_of(value: Any) -> str | None:
    if isinstance(value, ModuleType):
        # A module has no `__module__`; it *is* one. `molsysviewer.config.…` and
        # `molsysviewer.tools.…` are public entry points, so the walk has to descend
        # into submodules or it silently misses them.
        return getattr(value, "__name__", None)
    module = getattr(value, "__module__", None)
    return module if isinstance(module, str) else None


def _owned_by_molsysviewer(value: Any) -> bool:
    """Ours, and not behind the private door.

    `_private` is excluded by name rather than by reachability: a public module that
    imports `digest` re-exports it as `molsysviewer.<module>.digest`, so reachability
    alone would enter it. That single import accounted for 38 apparent public callables.
    """

    module = _module_of(value)
    if module is None:
        return False
    parts = module.split(".")
    return parts[0] == "molsysviewer" and "_private" not in parts


def _public_names(owner: Any) -> list[str]:
    """The names `owner` offers, by Python's own convention rather than by ours.

    For a module: `__all__` when it declares one — 38 do — and otherwise the
    non-underscore names *defined there*. The "defined there" test is what stops the
    walk from counting every imported helper as a new public callable of every module
    that imports it.

    For an instance: whatever `dir()` reports, since a method is defined on the class,
    not on the module the instance is reached through.
    """

    if isinstance(owner, ModuleType):
        declared = getattr(owner, "__all__", None)
        if declared is not None:
            return [name for name in declared if not name.startswith("_")]
        own_name = getattr(owner, "__name__", None)
        names = []
        for name in dir(owner):
            if name.startswith("_"):
                continue
            try:
                value = getattr(owner, name)
            except Exception:
                continue
            if isinstance(value, ModuleType) or _module_of(value) == own_name:
                names.append(name)
        return names

    return [name for name in dir(owner) if not name.startswith("_")]


def walk_public_surface(roots: dict[str, Any]) -> Iterator[PublicCallable]:
    """Every callable reachable from `roots` without passing through an underscore name.

    Instances are walked, not classes: `view.regions` is what a user holds, and reaching
    the manager through the instance is what makes it public. A class that is only ever
    constructed internally is therefore never visited, which is the whole point.
    """

    seen_objects: set[int] = set()
    seen_paths: set[str] = set()
    queue: list[tuple[str, Any, int]] = [(name, value, 0) for name, value in roots.items()]

    while queue:
        path, owner, depth = queue.pop(0)
        if id(owner) in seen_objects or depth > MAX_DEPTH:
            continue
        seen_objects.add(id(owner))

        for name in _public_names(owner):
            try:
                value = getattr(owner, name)
            except Exception:
                # A property that needs state we do not have is not a callable surface.
                continue

            child_path = f"{path}.{name}"
            if child_path in seen_paths:
                continue

            if callable(value) and not isinstance(value, type):
                if not _owned_by_molsysviewer(value):
                    continue
                seen_paths.add(child_path)
                module = getattr(value, "__module__", "?")
                yield PublicCallable(
                    path=child_path,
                    qualified_name=f"{module}.{getattr(value, '__qualname__', name)}",
                    module=module,
                    digested=_is_digested(value),
                    arguments=_user_arguments(value),
                )
            elif _owned_by_molsysviewer(value) and not isinstance(value, type):
                queue.append((child_path, value, depth + 1))


def build_inventory() -> dict[str, Any]:
    view = demo["dialanine"]
    view.widget.send = lambda _message: None  # type: ignore[attr-defined]

    # A `Region` and a `Selection` are public objects a user holds, but they are reached
    # by indexing a manager rather than by attribute access, so the walk cannot find them
    # on its own. Creating one of each puts their methods in the inventory; without this
    # the whole `view.regions[tag].*` surface is invisible.
    view.regions.add(selection="atom_index==[0,1]", tag="_inventory_probe")
    view.selections.add("_inventory_probe", atom_indices=[0, 1])

    roots = {
        "molsysviewer": molsysviewer,
        "view": view,
        "view.regions[…]": view.regions["_inventory_probe"],
        "view.selections[…]": view.selections["_inventory_probe"],
    }
    callables = sorted(set(walk_public_surface(roots)), key=lambda item: item.path)

    digesters = declared_digesters()
    exempt = [item for item in callables if item.path in DELIBERATELY_NOT_DIGESTED]
    undigested = [item for item in callables
                  if not item.digested and item.path not in DELIBERATELY_NOT_DIGESTED]

    missing: dict[str, list[str]] = {}
    for item in undigested:
        for argument in item.arguments:
            if argument not in digesters:
                missing.setdefault(argument, []).append(item.path)

    return {
        "callables": [item.as_dict() for item in callables],
        "totals": {
            "public_callables": len(callables),
            "digested": sum(1 for item in callables if item.digested),
            "undigested": len(undigested),
            "exempt": len(exempt),
            "declared_digesters": len(digesters),
            "missing_digesters": len(missing),
        },
        "undigested": sorted(item.path for item in undigested),
        "exempt": sorted(item.path for item in exempt),
        "missing_digesters": {
            name: sorted(paths) for name, paths in sorted(missing.items())
        },
    }


def baseline_of(inventory: dict[str, Any]) -> dict[str, Any]:
    """The part the guard pins: what is undigested, and which arguments are undeclared.

    Deliberately not the whole inventory. Adding a *digested* callable is free and should
    not touch a baseline file; adding an undigested one is the thing that has to be seen.
    """

    return {
        "totals": inventory["totals"],
        "undigested": inventory["undigested"],
        "missing_digesters": sorted(inventory["missing_digesters"]),
    }


def _report(inventory: dict[str, Any]) -> str:
    totals = inventory["totals"]
    missing = inventory["missing_digesters"]

    lines = [
        "Public API inventory (reachable from `import molsysviewer` and from a view)",
        "",
        f"  public callables      {totals['public_callables']:>5}",
        f"    digested            {totals['digested']:>5}",
        f"    undigested          {totals['undigested']:>5}",
        f"    exempt by design    {totals['exempt']:>5}",
        f"  declared digesters    {totals['declared_digesters']:>5}",
        f"  MISSING digesters     {totals['missing_digesters']:>5}"
        "   <- the size of the job",
        "",
    ]

    if missing:
        lines.append("Missing digesters, most demanded first:")
        ranked = sorted(missing.items(), key=lambda item: (-len(item[1]), item[0]))
        for name, paths in ranked[:40]:
            lines.append(f"  {len(paths):>3}x  {name:<32} e.g. {paths[0]}")
        if len(ranked) > 40:
            lines.append(f"  ... and {len(ranked) - 40} more")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the inventory as JSON")
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="rewrite the committed baseline the regression guard compares against",
    )
    arguments = parser.parse_args()

    inventory = build_inventory()

    if arguments.write_baseline:
        BASELINE_PATH.write_text(
            json.dumps(baseline_of(inventory), indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {BASELINE_PATH.relative_to(ROOT)}")
        return

    print(json.dumps(inventory, indent=2) if arguments.json else _report(inventory))


if __name__ == "__main__":
    main()
