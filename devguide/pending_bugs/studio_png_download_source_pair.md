---
summary: Studio PNG download guard times out in the Python 3.14 exact source-pair lane
issue: uibcdf/molsysviewer#198
status: partial
opened: 2026-10-09
closed:
severity: medium
verification: upstream
area: [studio]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Studio PNG download guard times out in the Python 3.14 exact source-pair lane

**Reported:** 2026-10-09, second Studio review and authorized refinement.

## What

Run 38000819781 on c92c2760 times out waiting for the Studio PNG download. Independent core 38000819783 passes 42/42. The cause is not established.

## How

Diagnose the actual PNG request/render/download path with bounded evidence, preserve original failure, and fix the mechanism rather than increasing the timeout or skipping the assertion.

## Why

The principal maintainer authorizes this refinement round before the next 0.25.0 candidate freeze. Both 1.0 publications remain paused. Consumer source: 01208af0 after the first Studio round. Implementation must retain real molecular/browser guards, native backend ownership and explicit qualification scope.

## What was refuted

Source signature inspection is not full scientific/artifact qualification. No publication is authorized by this implementation.

## Resolution

Dimension updates now change the PNG readout in place instead of replacing the
button between pointer-down and pointer-up. The real browser guard deliberately
holds the button during two dimension notifications, then downloads and checks
actual PNG dimensions/alpha. It passes locally in scoped and core runs. Rendering
failures and download initiation now produce bounded inline status/console evidence.

This establishes and guards a deterministic click-preservation defect. It does
not establish the cause of historical run 38000819781. Its raw failure is retained;
no timeout is increased and no assertion skipped. Review the next exact-source
hosted source-pair gate before closing this report or claiming hosted repair.

## Follow-up — 2026-10-10

Exact source a699f5b5 fails again in core browser run 38034284562, at
`studio-usability`: 30 seconds waiting for the PNG download. Source pair
38034284506 also fails on Linux; Windows and macOS pass. The eight guards
and individual Studio PNG/HTML browser check for the #206–#208 round pass
locally; that does not diagnose the hosted input/render/download failure.
The browser guard now retains pointer-down/up/click, current inline status,
disabled state and drawing-buffer dimensions if its download wait fails.
The wait and image byte/alpha assertions remain unchanged. Inspect the next
source's bounded evidence before claiming a hosted repair or closing #198.
