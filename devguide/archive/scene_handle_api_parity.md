---
summary: Complete inspection and editing parity for public scene handles
issue: uibcdf/molsysviewer#217
status: resolved
opened: 2026-10-10
closed: 2026-10-10
verification: inspected
area: [api,scene]
guard: tests/test_public_api_hardening.py
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Complete inspection and editing parity for public scene handles

**Reported:** 2026-10-10, final public API review with the principal maintainer.

## What

Expose detached `info()` on shapes, annotations, measurements and visual
interaction sets. Let annotation handles edit their text, style and anchor
through their existing manager. Provide `Region.set_tag()` and explicit sphere
anchor parameters on the manager shortcut.

## How

Delegate to the owning operation after public ArgDigest validation and a live
handle check. Retain `Region.rename()` and existing deprecated migration routes
in this development round. Layer attachment should accept regions through the
same owner and lifetime checks as other scene objects.

## Why

Users should be able to inspect and edit an object they just created without
switching unnecessarily to its manager. Named sphere parameters make existing
capabilities discoverable with Python introspection.

## What was refuted

No new detector, provider contract or graphic primitive is needed. These are
delegations to existing owners; Interactions remains experimental. The change
does not qualify installed packages or freeze the next candidate.

## Resolution

Implemented delegated detached info(), annotation handle editing, Region.set_tag(),
region layer attachment and explicit sphere anchors. The guard module checks
copy ownership, Undo/Redo, retired editing refusal, actual atom-anchored geometry
and named signature discovery. Related regression passes 376/376. Interactions
remains experimental; no candidate or package qualification is implied.
