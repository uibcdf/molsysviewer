---
summary: Studio loses an unfocused new-region name during session projection
issue: uibcdf/molsysviewer#202
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [studio, frontend]
guard: molsysviewer/js/tests/e2e/studio-list-workflows.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Studio final review — region

**Reported:** 2026-10-10, final Studio review with real pentalanine and Mol*/Chromium.

## What
The name of a region in preparation becomes empty when the field is unfocused and a canonical session projection repaints Regions.

## How
With real pentalanine, open New region, type unfinished-region, focus Saved Regions search, then apply real runtime region/selection summaries. The name becomes empty. Switching tabs alone without a repaint preserves it and is not the cause.

## Why
Background updates should preserve a user's creation draft. Store the name in the Regions panel model and clear it only on explicit completion/cancellation, with a real browser guard.

## What was refuted

Switching tabs alone without a repaint did not reproduce the loss. The cause is rebuilding the input without a model value during a canonical projection.

## Resolution

The new-region name lives in the Regions model instead of only the input DOM. The real browser guard leaves it unfocused, projects runtime summaries while visible and while hidden, then checks the retained value. Escape clears the draft before reopening the form.

**Executed:** 14/14 focused Python cases; TypeScript no-emit check; npm JS unit suite; real pentalanine/Mol*/Chromium Studio guard. These are source/development checks, not installed artifact qualification. The complete Python run and hosted gates retain their separate outcomes.
