---
summary: Evaluate shared GUI access to demos and recent sources
issue: uibcdf/molsysviewer#277
status: open
opened: 2026-10-29
closed:
verification: inspected
area: [standalone, studio, loading]
guard:
normative:
blocked_by: []
supersedes: []
---

# Evaluate demos and recent sources in the shared GUI

**Reported:** maintainer decision on 2026-10-29. Deferred to post-1.0.

## What

The maintainer accepts removing the Qt window menu without immediately moving
its demo catalogue and recent-source list into another GUI. Demos remain
available through `msv.demo` and `molsysviewer-qt NAME --demo`. Evaluate later
whether these extras are useful and where they fit: Studio > System, a future
Loader or the empty-view welcome flow. No new application menu is wanted.

## How

Review novice benefit, discoverability and visual density alongside
uibcdf/molsysviewer#265. Reuse the existing demo catalogue and MolSysMT system
registry. Define recent-source scope, persistence and clearing: per view,
notebook session or desktop installation. Keep server-side paths distinct
from browser-local files; do not expose another session's paths or silently
restore a saved source. Keep add/replace/append intention, source identity,
atom/structure selection and pairing explicit.

Use the same loading owner in Python, notebook and popup canvases. Static
exports must not offer unavailable backend loading. If adopted, qualify the
actual GUI routes and accessibility; do not substitute a second host loader.

## Why

The existing shared loading panel handles paths/PDB IDs but has neither a demo
picker nor a recent-source list. This is an intentional current scope decision,
not evidence that the capabilities are implemented in Studio. The Qt menu is
being retired to keep the scene UI shared and the window quiet.

Related: uibcdf/molsysviewer#35 retains human replacement receiving through
the remaining loading routes; #276 considers future hosts independently.

## What was refuted

Retiring a duplicate window menu does not imply immediately adding more
controls to Studio. A desktop-specific recent list cannot automatically become
a suitable notebook or remote-session history.

## Acceptance

Record an explicit decision for each capability: add, defer further or reject.
Any accepted GUI has an owner, source/history contract, availability wording
and executable guards. No new Studio panel or release gate is implied here.
