---
summary: Exported Studio shows inconsistent backend states and leaves shape creation pending
issue: uibcdf/molsysviewer#208
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [studio]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Exported Studio shows inconsistent backend states and leaves shape creation pending

**Reported:** Final Studio review with the principal maintainer, 2026-10-10.

## What

A real self-contained pentalanine export in Chromium lets Shapes submit creation, shows the missing-Python notice, then stays disabled in Creating… forever. Annotations incorrectly says Load a structure first while the molecule is drawn.

Observed on main a699f5b52729631643759942440c2afcb82e39f6 in the principal maintainer’s final Studio review.

## How

Project complete scene summaries and explicit backend availability. Reject unavailable mutations before entering pending state while preserving inspection and local camera/export actions.

## Why

Authorized pre-1.0 Studio closure. Candidate 0.25.0 remains unfrozen; both 1.0 publications remain paused. Preserve real Python/Mol*/Chromium regression evidence.

## What was refuted

A successful normal-path smoke check does not cover rejection, replacement or exported backend availability. Source and live browser evidence do not qualify a frozen installed artifact.

## Resolution

Panel/canvas snapshots now project loaded-system state, active selection and measurement settings consistently. Exported controllers override Interactions backend availability and reject unavailable correlated form mutations with an inline missing-session error; they retain the draft and leave pending state immediately. Ordinary missing-backend actions keep the existing notice. Local camera reset and PNG actions remain available.

The executed `studio-usability` guard opens its actual downloaded standalone HTML in Chromium with real Mol* rendering, checks Annotations does not falsely request a structure, submits a coordinate shape and verifies the inline error, retained tag and absence of Creating…, and checks Interactions calculation is disabled. The Python snapshot guard verifies matching live scene metadata/settings. This source/browser evidence does not qualify an installed artifact.
