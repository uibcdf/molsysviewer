---
summary: Consolidate quantity digesters on PyUnitWizard canonical paths.
issue: uibcdf/molsysviewer#33
status: partial
opened: 2026-08-13
closed:
verification: inspected
area: [argdigest, performance, units]
guard: tests/test_digestion_helpers.py::test_the_scalar_length_digesters_go_through_the_shared_boundary
normative:
blocked_by: []
supersedes: []
---

# Consolidate quantity digesters on PyUnitWizard canonical paths

**Reported:** 2026-08-13, while propagating PyUnitWizard's completed cheap-canonicity
work through MolSysSuite consumers.
**Status:** Open. The shared length helper is normative, but legacy digesters have not
been audited against it.

## What

Audit MolSysViewer's physical-magnitude digesters and consolidate compatible ones on
the existing `digest_length_quantity()` boundary and PyUnitWizard's canonical
normalization paths.

The existing units policy already requires `puw.ensure_quantity()` through the shared
helper for ordinary length arguments. The proposal closes the gap between that policy
and older digesters that still implement their own `check()`, `get_unit()`, and
`standardize()` sequences.

## How

Inventory production quantity digesters and group them by semantic contract: scalar
length, coordinate-like array, box, time, energy, dimensionless vector, or special
union/list input. Migrate plain length arguments to `digest_length_quantity()` when its
shape, optionality, and error behavior match exactly.

For array and interactive paths, use `ensure_quantity()` as the default boundary.
Introduce `has_unit()` only after a representative benchmark shows remaining fixed
overhead and only when the local code must also normalize shape or dtype. Preserve the
viewer `ArgumentError` translation and use `get_value(..., to_unit=...,
value_type=..., dtype=...)` at the Mol* wire boundary.

## Why

The normative policy says not to hand-roll
`parse → is_quantity → check → standardize → raise`, yet source inspection finds many
legacy digesters that predate the shared helper. That duplication can drift in accepted
inputs, exception types, canonical units, and performance.

PyUnitWizard's optimized `ensure_quantity()` means the shared implementation now has a
cheap canonical path. Consolidation can therefore improve consistency without placing
backend-specific unit logic in MolSysViewer.

## What is measured and what is assumed

Measured upstream and in a representative MolSysViewer length digester: canonical
inputs benefit from the optimized PyUnitWizard boundary, while non-canonical inputs
retain validation and conversion.

Assumed: some remaining legacy digesters are both compatible with the shared helper
and frequent enough for the change to matter. The audit must distinguish those from
specialized or cold paths before implementation.

## What was refuted

- A blanket replacement of all quantity digesters is unsafe. Boxes, coordinates,
  union-valued arguments, and dimensionless directions have different contracts.
- Bare numbers must not become an optimization fallback; the units policy explicitly
  rejects them.
- `has_unit() is False` is not a dimensionality check. Untrusted non-matches and
  undecidable inputs return to the general validation route.
- `skip_digestion=True` is not a unit fast path. It remains restricted to internal
  delegation after every argument invariant has already been established.

## Scope and exclusions

In scope are Python argument digesters and Python-to-Mol* magnitude extraction. Out of
scope are frontend payload-schema changes, a new default unit for bare values, global
unit-configuration policy, and unrelated rendering performance.

## Acceptance criteria

- Production magnitude digesters are inventoried and classified by semantic contract.
- Plain length digesters use the shared helper when behavior is identical.
- Specialized migrations have canonical, compatible non-canonical, incompatible-unit,
  shape, batch, and local-error regression coverage as applicable.
- Representative interactive paths are benchmarked before adding explicit canonical
  branches.
- Wire serialization converts explicitly to angstroms with PyUnitWizard extraction
  controls rather than manual array/scalar wrapping.
- Focused tests and the normal MolSysViewer full-suite gate pass.
- Durable local rules are incorporated into `devguide/units_and_quantities.md`; the
  canonical API rules remain in `PYUNITWIZARD_GUIDE.md`.

## Dependencies and risks

The work depends on the PyUnitWizard version documented by the synchronized guide. The
main risks are changing local exception types, accidentally accepting bare magnitudes,
and treating dimensionless direction vectors as lengths.


---

## Audit and first slice — 2026-09-02

The proposal asked for the inventory before implementation. Here it is, over the 69
digesters that touch a physical magnitude: **17 already use the shared helper, 52 hand-roll
the sequence.** Of those 52, far fewer are migratable than the count suggests:

| group | n | migratable to the scalar helper |
| --- | ---: | --- |
| `[L]¹` scalar, **pure pattern** | **3** | yes — line-for-line identical |
| `[L]¹` scalar, extra branches | 6 | one at a time, each a judgement |
| `[L]¹` array (box, coordinates, …) | 11 | no — different contract |
| no declared dimensionality | 28 | mostly not quantities at all |
| `[L]²`, `[T]`, `[K]` | 4 | own contracts |

**Done: the three pure ones** — `distance`, `length`, `z0`. Each was the same twelve lines
and each raised with `message=None`, so a caller passing `3.5` was told only that the
argument was wrong. They now say which unit to add and which mistake it prevents. That is
the user-visible half of this proposal, and it was free.

**Not done, deliberately: the six with branches** — `bond_length` (6 extra conditions),
`threshold` (4), `distance_threshold` (4), `switch_distance` (3), `cutoff_distance` (2),
`max_bond_length` (1). Almost all of them are caller-conditional optionality: `cutoff_distance`,
for instance, returns `None` only when the caller is a MolSysMT form conversion. Each is a
small decision about when `None` is valid, and getting one wrong changes what the public
API accepts. Six such decisions days before freezing a release candidate is the wrong
trade; they are cheap and safe to do after.

**Also outstanding:** the 28 with no declared dimensionality have not been individually
confirmed as non-quantities. That is the remaining inventory work, and it is what would
turn this from `partial` into `resolved`.

Guard: `test_the_scalar_length_digesters_go_through_the_shared_boundary`, mutation-verified
against restoring each of the three. It pins the *message*, not the plumbing — the policy
exists because a bare number is a silent nm/angstrom scale error, and an error that does
not name a unit leaves the caller guessing which one this API wanted.

## Second slice — 2026-09-02

The remaining six scalar `[L]` digesters were re-examined before deciding whether to
migrate them, and the answer changed twice.

**They are healthier than the pair that produced #69.** All six declare a dimensionality,
so none accepts seconds, none reads a bare numeric string as radians, and none returns a
non-numeric string unchanged. `extra_radius` and `min_radius` were the outliers precisely
because they declared none — which is why the audit found a crash there and not here.
Migrating the six is therefore consistency work, not defect work, and it is safe to leave
until after the release window.

**One of them was broken anyway, in a way the smell test missed.** `bond_length` has a
caller-conditional branch for functions taking a list of lengths, and this copy had drifted
from MolSysMT's original into a version that could never return: `output = []` sat inside
the loop, so only the last element would have survived, and the guard asked
`puw.check(bond_length, ...)` about the whole list rather than the element, which is always
`False`. Every list was rejected.

It is unreachable from MolSysViewer — no caller here ends in `add_harmonic_bond_force`,
which is a MolSysMT function. Repaired by synchronizing with the original rather than
deleted, so the copy stays faithful, and guarded.

**The lesson is not about digesters.** This directory is a copy of MolSysMT's, and the
copy drifted. On the same day, the same shape of problem appeared twice more: a CSS rule
they had already found and we had not, and a conda recipe defect reported to them that
this project then turned out to share. Duplicated infrastructure between sibling
repositories is costing this ecosystem the same defect two and three times over. That is
worth its own decision, and it is not this proposal's to make.

**Still open:** the five remaining branched digesters, as consistency work.

## Third slice — 2026-09-02 — the remaining five cannot be consolidated, and why

Setting out to migrate the last five branched scalar-length digesters, the premise turned
out to be wrong. **None of `threshold`, `distance_threshold`, `switch_distance`,
`cutoff_distance` or `max_bond_length` corresponds to any argument in MolSysViewer's public
API.** Zero signatures carry those names, and outside the digester directory they are
mentioned essentially nowhere.

They are copies of MolSysMT's, and they say so in their own code. `threshold` accepts a
value only when the caller is in one of two hard-coded allow-lists, and every name in them
is a MolSysMT function — `molsysmt.structure.get_contacts.get_contacts` and the like.
Nothing in this package can be in those lists, so the digester rejects everything it is
given. Consolidating them onto the shared helper would be polishing code that cannot run.

Two are worse than dead. `switch_distance` and `cutoff_distance` raise **AttributeError**
when called without a `caller`, because this copy dropped the `caller is not None` guard
that MolSysMT's has. `threshold` also carries `molsysmt.thirds.nglview...` where theirs
says `molsysmt.third_party.nglview...` — a stale name that would not match even if a
MolSysMT caller reached it. More drift, of the kind `uibcdf/molsysviewer#70` is about.

### How much of the directory is in this state

| | |
| --- | ---: |
| digesters in the directory | 581 |
| whose name appears in a signature somewhere in this package | 308 (53%) |
| **with no appearance at all** | **273 (46%)** |

The estimate comes from scanning parameter names across the package and is a heuristic, so
treat it as approximate. Spot-checked in both directions: `angle_threshold`, `acceptors`,
`alternate_location` and `N_terminal` have zero mentions outside the directory, while
`selection`, `extra_radius` and `duration` have 457, 32 and 51.

### What this proposal can and cannot now conclude

The consolidation this proposal asked for is **done for everything it can apply to**: the
three pure digesters, plus `extra_radius` and `min_radius`, which were reachable and
carried real defects (`uibcdf/molsysviewer#69`).

What remains is not consolidation. It is the question of what a package should do with
roughly half a directory copied from a sibling and unreachable here — delete, keep
synchronized, or leave. That is `uibcdf/molsysviewer#70`'s question, and this measurement
is the first instalment of the "separate legitimate divergence from drift" work it asks
for. It is **not this proposal's to answer**, and deleting 273 files is not a change to
make without a decision.

### Correction — 2026-09-02 — the 46% figure above is wrong, and so was the spot-check

The measurement recorded earlier the same day said **273 of 581 (46%)**. It was produced by
asking whether each digester's name appears in a signature, which is not what reachability
means here, and it is wrong in both directions.

**It missed the largest source of reach.** ArgDigest resolves a digester by argument name
at call time — `plan.digesters.get(argname)` for each bound parameter. The `get`-shaped
methods take `**kwargs` and forward to `msm.get`, and no domain is declared for them, so
**every MolSysMT attribute and alias is a name that can arrive here**: 278 of them, none of
which appears in any signature of ours. `alternate_location` was one of the four names the
spot-check offered as confirmed-dead; it is a MolSysMT attribute, and
`view.get(alternate_location=True)` reaches its digester. The spot-check confirmed nothing
— it re-ran the same flawed test.

Two smaller misses: the scan skipped `*args`, so `others` looked dead, and names that
arrive as dictionary keys rather than parameters (`molstar_color_theme`, `size_scheme`)
were invisible to it.

**The claim it was made to support survived.** The five branched digesters really are
unreachable, but the earlier session's evidence for that was contaminated too: a runtime
recorder patched `load_argument_digesters` globally, and MolSysMT uses ArgDigest as well,
so it recorded *their* lookups as ours. `threshold` showed up as consulted for that reason.
Attributed by config source, `threshold` is theirs; ours is never consulted.

The corrected figure, from six independent tests rather than one heuristic, is **120 of
581**. What was done with them, and the evidence for each, is in
`devtools/quarantine/README.md`.
