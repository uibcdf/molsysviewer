"""The public API inventory, pinned so it can only change on purpose.

Gate 9 of the pre-1.0 plan asks that every public callable carry `@digest`. Its first
deliverable is not the decorating: it is knowing what "public" means here, closed as a
set, so the remaining work has a size and cannot quietly grow while it is being done.

`devtools/public_api_inventory.py` produces that set by walking what a user can actually
reach. This holds it still. Both directions fail on purpose:

- something **new and undigested** appears — the surface grew without its contract;
- something **disappeared** — real progress, and the baseline must be regenerated with it
  so the inventory stays closed rather than becoming a stale ceiling.

Regenerate with `python devtools/public_api_inventory.py --write-baseline`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "devtools"))

from public_api_inventory import (  # noqa: E402
    BASELINE_PATH,
    baseline_of,
    build_inventory,
    declared_digesters,
)


@pytest.fixture(scope="module")
def inventory():
    return build_inventory()


@pytest.fixture(scope="module")
def baseline():
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def test_no_public_callable_becomes_undigested_without_being_recorded(inventory, baseline):
    current = set(inventory["undigested"])
    recorded = set(baseline["undigested"])

    appeared = sorted(current - recorded)
    assert appeared == [], (
        "these public callables are undigested and not in the inventory. Either decorate "
        "them and declare their arguments, or regenerate the baseline to record the "
        f"decision: {appeared}"
    )

    disappeared = sorted(recorded - current)
    assert disappeared == [], (
        "these are no longer undigested — regenerate the baseline so the inventory keeps "
        "reporting the real size of the remaining work: "
        f"python devtools/public_api_inventory.py --write-baseline ({disappeared})"
    )


def test_no_argument_name_arrives_without_a_digester(inventory, baseline):
    """The count that matters. Decorating is one line; declaring the argument is the job.

    `STRICTNESS = "warn"`, so an argument with no digester warns on every call rather than
    failing. A new one is therefore invisible at runtime and has to be caught here.
    """
    current = set(inventory["missing_digesters"])
    recorded = set(baseline["missing_digesters"])

    assert sorted(current - recorded) == [], (
        "new public arguments with no digester: "
        f"{sorted(current - recorded)}"
    )
    assert sorted(recorded - current) == [], (
        "digesters were written for these — regenerate the baseline: "
        f"{sorted(recorded - current)}"
    )


def test_the_totals_are_the_ones_the_gate_is_tracking(inventory, baseline):
    assert inventory["totals"] == baseline["totals"]


# --- what the inventory means, pinned against the ways it could quietly stop meaning it


def test_the_private_package_is_never_public(inventory):
    """A public module that imports `digest` re-exports it under its own name.

    Reachability alone therefore walks straight into `_private`, and that one import
    accounted for 38 apparent public callables before it was excluded.
    """
    leaked = [item["path"] for item in inventory["callables"]
              if "_private" in item["module"].split(".")]

    assert leaked == []


def test_imported_names_do_not_count_as_a_modules_own_public_surface(inventory):
    """`molsysviewer.<module>.digest` is ArgDigest's decorator, not our public API."""
    paths = {item["path"] for item in inventory["callables"]}

    assert not any(path.endswith(".digest") for path in paths)


def test_objects_reached_by_indexing_a_manager_are_in_the_surface(inventory):
    """A `Region` is public, but it is reached with `view.regions[tag]`, not by attribute.

    Nothing in a plain attribute walk finds it, so the whole `Region` surface would be
    missing from the inventory — and it is a surface users touch constantly.
    """
    paths = {item["path"] for item in inventory["callables"]}

    assert any(path.startswith("view.regions[…].") for path in paths)
    assert any(path.startswith("view.selections[…].") for path in paths)


def test_the_baseline_is_the_shape_the_guard_compares(inventory, baseline):
    assert baseline_of(inventory).keys() == baseline.keys()


def test_every_recorded_missing_digester_really_has_no_module(baseline):
    """The digester inventory is read off the filenames, so a rename must show up here."""
    declared = declared_digesters()

    assert declared, "no digesters found — the digester directory moved"
    assert not (set(baseline["missing_digesters"]) & declared)


def test_no_exemption_is_a_ghost(inventory):
    """An exemption naming nothing is an unexamined claim that reads as a decision.

    It is also how a real exemption goes stale: the callable is renamed, the entry stays,
    and the inventory silently stops covering it. Caught while writing the list — one
    entry named a method that does not exist.
    """
    from public_api_inventory import DELIBERATELY_NOT_DIGESTED

    paths = {item["path"] for item in inventory["callables"]}
    ghosts = sorted(set(DELIBERATELY_NOT_DIGESTED) - paths)

    assert ghosts == [], f"exemptions matching no public callable: {ghosts}"


def test_every_exemption_gives_a_reason():
    from public_api_inventory import DELIBERATELY_NOT_DIGESTED

    silent = [path for path, reason in DELIBERATELY_NOT_DIGESTED.items()
              if not reason or len(reason) < 20]

    assert silent == [], f"exemptions without a usable reason: {silent}"


def test_no_digester_is_written_for_a_var_parameter_name():
    """`args` and `kwargs` are not argument names; they are the absence of them.

    Thirteen `shapes` forwarders take `*args, **kwargs` and hand them to a sub-manager
    method that has a closed signature and its own `@digest`. Decorating a forwarder was
    tried and measured: nothing is digested — ArgDigest digests the empty `args` tuple and
    leaves the `**kwargs` keys in the mapping, so `tag` and the rest never reach their
    digesters — and every call emits `DigestNotDigestedWarning`.

    That warning made `args` look like a missing digester wanted by thirteen callables.
    Writing one would silence a signal that is correctly saying those functions should not
    be decorated, which is why this test exists rather than a `digest_args`.
    """
    forbidden = {"args", "kwargs"} & declared_digesters()

    assert forbidden == set(), (
        f"a digester was written for {sorted(forbidden)}; the warning it silences is "
        "telling you a pure forwarder is decorated, and the fix is to undecorate it"
    )


def test_a_pure_forwarder_is_never_decorated():
    """Decorating one is silent debt: it digests nothing and warns on every call.

    Two `add_pharmacophore_features` aliases carried `@digest` for months doing exactly
    that. Nobody saw the warning because the only test that reaches them passes
    `skip_digestion=True`, which turns the decorator off.
    """
    import ast

    offenders = []
    for path in sorted((ROOT / "molsysviewer").rglob("*.py")):
        if "js" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.FunctionDef):
                continue
            if not (node.args.vararg and node.args.kwarg):
                continue
            named = [a.arg for a in node.args.args if a.arg != "self"]
            named += [a.arg for a in node.args.kwonlyargs if a.arg != "skip_digestion"]
            if named:
                continue  # it declares something of its own, so it is not a pure forwarder
            if any("digest" in ast.unparse(d) for d in node.decorator_list):
                offenders.append(f"{path.relative_to(ROOT)}:{node.name}")

    assert offenders == [], (
        "these take only *args/**kwargs and are decorated, so they digest nothing and "
        f"warn on every call: {offenders}"
    )
