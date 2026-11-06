---
summary: Canvas popup omits the existing addon catalogue from its initial snapshot
issue: uibcdf/molsysviewer#300
status: resolved
opened: 2026-11-05
closed: 2026-11-05
severity: high
verification: reproduced
area: [addons, popup]
guard: tests/test_popup_snapshot.py::test_canvas_popup_inherits_current_addon_catalogue_without_replaying_widgets
normative: devguide/addon_panel_widget_contract.md
blocked_by: []
supersedes: []
---

# Canvas popup starts without the discovered addons

## What

An actual Jupyter/anywidget canvas popup renders 1TCD but its Add-ons manager
says no analytical addons are registered. The original notebook lists all five
installed addons, including MolSysMT tools. A later catalogue refresh can mask
the omission. Source runtime ecf4635e and checkpoint f31cf31a reproduce it.

## How

The canonical canvas projector omits addon catalogue/context metadata that the
panel projector includes. The interactive popup uses that Python snapshot;
it cannot reconstruct earlier discovery from a frontend replay journal.
The real Jupyter receiving failure is retained separately from the initial
test-fixture API mistake and the host's unrelated debugger error.

## Why

The canvas popup is a peer view of the scientific scene with the same addon
availability. Existing widget lifecycle, targeted routing and stylesheet
contracts in closed #245/#298 remain required; neither covered this metadata
bootstrap omission. The archive record for #245 was reviewed for that question.

## Correction and receiving

Canvas and panel projectors share current addon catalogue/context builders,
without replaying widget instances or their executable state. Static export
builds the addon projection once. The demo-backed pytest guard compares
catalogues and selection context, checks defensive copies and export uniqueness;
snapshot purity/completeness and addon regressions pass (78 cases, one legacy
entry-point omission). Another 315 host protocol/endpoint cases pass. Actual
Jupyter/canvas/Studio popup receiving completes six checks, including two
exact native edits and convergence on 3,817 atoms. The existing three-scenario
scientific popup guard also passes. The [receipt](../jupyter_addon_popup_receiving_20261105.json)
retains source hashes, the independent Jupyter debugger baseline and the
original failures. Human review is explicitly postponed; exact-head CI,
MolSysMT owner integration and installed qualification remain separate.
