---
summary: The generated capability audit advertises three removed public methods, and prefix matching hides one of them behind ten unrelated names.
issue: uibcdf/molsysviewer#79
severity: medium
status: resolved
opened: 2026-09-04
closed: 2026-09-04
verification: measured
area: [process, tooling]
guard: tests/test_capability_audit.py::test_every_declared_api_entry_resolves_on_its_own
normative:
blocked_by: []
supersedes: []
---

# A generated document making the claim it exists to prevent

**Measured:** 2026-09-04, while starting [#65](evidence_a_stable_capability_has_not_earned.md).

`devguide/capability_audit.md` opens by saying it exists so that "README, the
documentation, the paper and a release cannot make slightly different claims about the
same thing". It is currently the one making the wrong claim.

## What

Its Public API column lists `view.get`, `view.select` and `view.convert`. None of the three
exists. All were removed in the 0.22 API simplification and their removal is documented in
[`migrating_to_0_22.md`](../../docs/content/user/introduction/migrating_to_0_22.md).

Regenerating does not fix it — `python devtools/capability_audit.py --write` produces no
diff. The `api=` tuples in `devtools/capability_audit.py` are authored, and the header's
promise that "everything else is read from the repository" does not extend to checking that
what is declared still exists.

## Two failure modes, and why the second is the one that matters

**Dead entry.** `view.convert` matches nothing in the public API inventory.

**Masked entry.** `view.get` does not exist either, but `_api_evidence` matches by prefix,
so it absorbs ten unrelated methods that merely begin with the same characters:

```
view.get -> view.get_camera_snapshot, view.get_coordinates,
            view.get_last_active_selection_event, view.get_last_click_event,
            view.get_last_context_action_event, view.get_last_context_event,
            view.get_last_hover_event, view.get_last_measurement_created_event,
            view.get_last_tool_state_event, view.get_panel_mode_state
```

Ten frontend event accessors are counted toward the MolSysMT integration row, whose
provenance the audit declares as "MolSysMT (scientific authority)". They are nothing of the
kind. The row advertises a removed method *and* reports a `Public` count inflated by
methods belonging to another authority entirely.

The masking is what defeats the obvious guard: a check asking "does this prefix match
anything" passes for `view.get`. That guard would have been written, would have gone green,
and would have certified the defect.

## The distinction the data already carries

Punctuation. An entry ending in `.` is a namespace and needs at least one member; an entry
not ending in `.` names one callable and must resolve exactly. Nothing new has to be
declared — the table is already written this way.

Applied to the current 34 entries, that rule flags exactly the three above and produces no
false positives.

## Why

The audit is what the release gate and the paper read. A wrong row here is not a stale
document; it is the thing the other documents are checked against.

It is also our own loose end: this session removed the three methods and left the audit
advertising them. Nothing caught it because nothing was watching this column at all.

## What is measured and what is assumed

**Measured** — the three dead names and the ten masked matches, against
`public_api_inventory.build_inventory()` on 2026-09-04; that regeneration produces no diff;
that the namespace/exact rule yields no false positives on the other 31 entries.

**Not established** — whether any other generated document in the devguide declares names
it does not resolve. Only the capability audit was examined.

## What was refuted

**"Regenerate it."** Regeneration is what produces the wrong table; the authored tuples are
the input, not the output.

**"Check that each `api=` prefix matches something."** Passes for `view.get`, which is the
one that is actively misleading.

## Acceptance criteria

1. The three dead entries are gone from `CAPABILITIES`.
2. A guard fails when an `api=` entry that names a callable does not resolve exactly, and
   when one that names a namespace has no members.
3. The guard is mutation-verified against both shapes: a dead exact name, and a name masked
   by a longer unrelated sibling.

## Resolution

**Closed 2026-09-04.** The three dead entries are gone from `CAPABILITIES`, and the row
counts they were inflating fell to the truth: MolSysMT integration from 17 public
callables to 7 (13 digested to 3), Selections from 28 to 21. More than half of the
MolSysMT row was `view.get` absorbing frontend event accessors.

The guard is `test_every_declared_api_entry_resolves_on_its_own`, added beside the
row-level `test_every_row_names_a_public_api_that_exists` it corrects rather than
replacing it — the older one still catches a row that matches nothing at all.

Mutation-verified against all three shapes, each restored with `cp`:

| mutation | result |
|---|---|
| dead entry — `view.convert` put back | 2 failed |
| masked entry — `view.get` put back, matching 10 live siblings | 2 failed |
| empty namespace — `view.nonexistent.` added | 3 failed |

The masked case is the one that matters: it is the shape the pre-existing guard passed.

**Scope checked and clean.** The doc sources had already been migrated to
`view.whole.select` and `view.whole.get`; only `docs/_build/`, which is git-ignored, still
shows the old names. The capability audit was the single place still advertising them.
