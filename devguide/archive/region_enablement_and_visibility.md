---
summary: Separate region enablement from visibility and make Hide consistent
issue: uibcdf/molsysviewer#167
status: resolved
opened: 2026-10-06
closed: 2026-10-06
verification: inspected
area: [regions, visibility, studio, state]
guard: molsysviewer/js/tests/e2e/composite-load.e2e.ts
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Separate region enablement from visibility and make Hide consistent

**Reported:** 2026-10-06, human review and principal-maintainer design approval.

## What

Add `Region.enable()` / `disable()` and read-only `enabled`. An enabled hidden
region masks its atoms on Whole and hides its own representations in every
representation state. Disabling suspends its visual contributions, including
region-owned colors and Whole constraints, while preserving hidden state,
identity, selection, style and dependencies. Re-enabling reapplies them.

## How

Python owns independent `enabled` and `hidden` booleans. `_active` retains its
existing retirement meaning. Runtime, Studio, history, state/session, transfers,
rebuild and popup/static projections share that authority. Missing `enabled` in
older documents means true. Validate booleans before scene mutation.

Show/hide while disabled changes the saved visibility request without enabling
the region. Layers and bulk visibility do likewise. Disabling the isolated
region releases its isolation; `show_only()` requires an enabled region and
otherwise rejects before mutation. Its return/temporary-isolation design remains
for the next maintainer discussion. Other representations and overlays retain
their independence. Whole visibility remains independent.

Disabled selections and dynamic recipes remain available to queries and derived
regions. No extra coordinate arrays or atom masks are saved. Color contributions
are retained by owner and excluded from the resolved map while disabled.

## Why

The same Studio Hide removed unrepresented caffeine from Whole but revealed it
underneath an orange own representation. The user expects consistent hiding and
approved explicit suspension as the action that restores the Whole fallback.

## What was refuted

Using `_active=False` for suspension would retire region handles. Removing the
region would lose its identity and dependencies. Hiding every overlapping
representation would violate the agreed independent-region contract. A browser
only toggle would lose Python, persistence and history authority.

## Resolution

Python, runtime and Studio now share independent enablement and visibility.
State v2, session reopening, history, copies/extraction, rebuild and popup
projections preserve disabled configuration. Older state records default to
enabled. Invalid enablement and disabled isolation reject before mutation.
Region-owned color resolution ignores disabled owners without deleting layers;
dynamic recipes and dependent selections remain current.

The composite-loading browser guard now drives real demo regions through Python
and Studio, checks actual Mol* Whole masks and independent overlapping visuals,
and exercises None/Inherit/Own transitions, disabled colors, saved sessions and
isolation release. Supplemental Python regression coverage lives in
`tests/test_region_enablement.py`. The normative contract is absorbed by
`devguide/scene_contracts.md` §A.3/A.4 and §B.2/B.3.

Focused Python tests pass (12); the selected follow-up passes 264 tests, and
the complete JS unit lane passes 322. All 39 core browser suites pass across
the initial 26 passing suites and the remaining 13-suite follow-up after
updating one stale tooltip assertion. This is not one clean full-core run.
The once-run Python full suite had eight failures; their diagnosed causes and
passing selected follow-ups are retained in
`devguide/region_enablement_20261006.json`. It was not repeated.

Human retest of the new Hide/Enabled behavior remains pending. The temporary
Show Only/return-control design remains for discussion; this change only
integrates enablement with the existing isolation behavior. No release or
installed-package qualification is claimed.
