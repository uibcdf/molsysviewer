---
summary: Retire the MolSysMT addon from MolSysViewer while retaining its native backend
issue: uibcdf/molsysviewer#186
status: resolved
opened: 2026-10-09
closed: 2026-10-09
verification: reproduced
area: [addons, interactions]
guard: tests/test_addons.py
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Retire the MolSysMT addon from MolSysViewer while retaining its native backend

**Reported:** 2026-10-09, source review and real Mol*/Chromium Studio audit.

## What

The installed MolSysMT entry point currently exposes an addon with 8 panels, 18 sections and 5 actions, duplicating the native scientific surface. Diego explicitly authorizes retiring this addon during the Studio review.

Provider follow-up uibcdf/molsysmt#354 is closed with source entry-point and
documentation reconciliation. Published bytes and tags are not changed.

## How

Exclude the legacy provider from automatic discovery and reject explicit legacy registration before import. Retain native MolSysMT-backed loading, interactions and scientific operations; preserve domain addons. Remove obsolete consumer bridges and document the migration.

## Why

The Studio card is a public interactive surface being reviewed before 1.0.

## What was refuted

No claim of installed artifact qualification is made by this development review.

## Resolution

Automatic discovery skips the legacy MolSysMT entry point before import; explicit namespace/module registration refuses it with the native route. Native scientific calculations and domain addons remain available. The guard proves pre-load discovery exclusion, registration refusal and a real native hbonds calculation. Consumer tutorials migrate legacy addon editing calls. Provider uibcdf/molsysmt#354 is closed in source dfdb31489c3a7dce921fa7b1df9e3fcd24c1f4f6; this is not a claim about new published provider bytes.

Source validation and its limits are recorded in
[the Studio integration review](../studio_review_20261009.md).
0.25.0 remains unfrozen and both 1.0 publications remain paused.
