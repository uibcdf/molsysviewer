# Quarantine — argument digesters with no reachable caller

These files are **not deleted yet, and not importable**. `devtools/` is outside the
distributed package (`pyproject.toml` ships `molsysviewer*` only), so nothing here is
loaded, shipped, or resolvable by ArgDigest. They sit here so the removal can be undone
with one `git mv` if any of the evidence below turns out to be wrong.

## What they are

`molsysviewer/_private/argdigest/argument/` was seeded by copying MolSysMT's digester
directory wholesale. ArgDigest resolves a digester by *argument name*: on every call it
looks up `plan.digesters.get(argname)` for each bound parameter. A digester whose name no
argument can ever carry is therefore inert — it is imported at load time and never
consulted.

These 120 are that set.

## Why each one is here

A name was quarantined only if it failed **all six** tests. The union of the first five is
what "reachable" means; the sixth is the check that the union was right.

| # | test | how it was measured |
| - | ---- | ------------------- |
| 1 | not a public argument | `devtools/public_api_inventory.py` walks the surface reachable from `import molsysviewer` and from a view; 271 distinct argument names |
| 2 | not a MolSysMT attribute or alias | the `get`-shaped methods take `**kwargs` and forward to `msm.get`, so its 278 attribute names and aliases are all reachable here |
| 3 | `msm.get` refuses it | probed directly, all 120 against `element` in atom/group/system: **0 accepted** |
| 4 | never consulted at runtime | the digester map was wrapped in a recording dict for a full suite run, *attributed by config source* so MolSysMT's own lookups are not counted |
| 5 | referenced by no surviving digester | transitive closure over `digest_*` references between the files |
| 6 | mentioned nowhere at all | every identifier in `molsysviewer/`, `tests/`, `docs/`, `devguide/`, `sandbox/`, `devtools/` |

## The check that this changed nothing

`STRICTNESS = "warn"`, so a missing digester warns and passes the value through — a
removal that broke something would be quiet. It was made loud instead: with `STRICTNESS`
temporarily set to `"error"`, a missing digester raises.

The full suite was run that way after the move. **1663 passed, zero `No digester for`.**
The single failure was `test_the_totals_are_the_ones_the_gate_is_tracking`, reporting
`declared_digesters: 461` against a baseline of 581 — the inventory gate doing its job.
`test_no_argument_name_arrives_without_a_digester` passed, and the inventory still reports
**0 missing digesters** across all 479 public callables.

## Restoring one

    git mv devtools/quarantine/argdigest_argument/<name>.py \
           molsysviewer/_private/argdigest/argument/<name>.py
    python devtools/public_api_inventory.py --write-baseline

## What is deliberately still here

192 of the 461 surviving digesters correspond to no *named* public argument. They stay
because they are reachable anyway: `view.get(b_factor=True)` and its 277 siblings arrive
through `**kwargs`, and test 3 is what separates them from these 120.
