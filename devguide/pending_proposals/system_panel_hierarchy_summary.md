# Project the molecular hierarchy so the System subpanel obeys Contract S1

**Proposed 2026-08-01, from the panel pop-out smoke test: every Studio subpanel
renders in the popped-out window except System, which is empty.**

## It is a regression, and knowing that changes the options

**It used to work.** Before the R2 rework (`f023983e`), both pop-outs received
`messages: [...commandLog]` — the whole command log, `load_molsys_payload`
included. The panel window therefore built a complete structure into its hidden
canvas, and System rendered there exactly as it does in the floating panel.

R2 replaced that with the canonical Python-built snapshot, split into a canvas
projection (with geometry) and a panel projection (UI state, no geometry). The
split is right, and the rule it encodes — "no molecular payload, topology,
coordinates, or structure-dependent visual operations may appear here" — is right
too. What nobody reconciled is that **System is a structure-dependent panel
section**, so the rule quietly excluded it from the window it lives in.

So the old behaviour was not free: it worked by shipping a second full copy of the
structure into a window with no canvas to draw it on, which is precisely the cost
R2 stopped paying. Restoring it would undo a real improvement. The proposal below
gets the function back *without* the cost.

## What is actually wrong

It is not a rendering bug. **System is the only subpanel that does not obey
Contract S1.**

Every other subpanel — Regions, Measures, Annotations, Shapes, Layers, Whole,
Selections — renders from a summary Python computes and pushes, which is why they
all populate in a panel-only window from `_build_panel_snapshot` alone. System
renders from the Mol\* `Structure` object: `captureCurrentStructure` calls
`groupPanel.setStructure(structure)`, and `SystemPanel.rebuild` builds one
`GroupStrip` per chain from it.

A panel-only endpoint has no structure **by design** — its snapshot carries UI
state and deliberately no geometry, and `test_a_panel_popup_snapshot_never_starts_a_molecular_stream`
pins that. So System cannot work there, and no amount of visibility fixing will
change it. The two earlier fixes in this area (the welcome card, then panel
visibility) were the same premise error at the window level; this is the same
error at the subpanel level, and the last of them.

## Why it is worth doing rather than papering over

The data System needs is **per group, not per atom**. Its strips are built from
`GroupSelectionItem[]` (`buildGroupItemsFromStructure`), one entry per group with
chain, molecule and component metadata. For 181L that is 302 entries; for a large
system it scales with groups, which is orders of magnitude below geometry. It is a
legitimate UI summary, not a structure in disguise, so it does not violate the
reason the panel snapshot excludes geometry.

Python already holds every field, through MolSysMT, and holding it is what
Contract S1 says it should be doing.

## Proposal

1. A `set_hierarchy_summary` op carrying the group-item list, added to
   `_build_panel_snapshot` and to the `_sync_*_runtime` family like every other
   summary — including the `ready` re-send that S1 requires, or the panel renders
   empty on every fresh attach.
2. `SystemPanel` / `GroupStrip` render from that list. They already store
   `groupItems` as their primary data; the `Structure` reference they also keep is
   used for hover and selection resolution and has to be made optional, which is
   the real work in this proposal.
3. The host keeps deriving the same list locally, so nothing regresses when a
   structure *is* present. The Python projection and
   `buildGroupItemsFromStructure` must then produce the same shape — two producers
   of one shape, so a test has to pin their agreement, or they will drift (§0).

## Interim, if this is not done soon

Show a short line in the System tab of a panel-only window saying the hierarchy
lives with the canvas. Not a fix, but honest: today the tab looks broken rather
than out of scope, and a user cannot tell those apart.

## Acceptance

- The panel pop-out renders System with its chain strips, from the snapshot alone.
- A test asserts the Python projection and `buildGroupItemsFromStructure` agree on
  the same system, since nothing else forces them to.
- The snapshot stays UI-sized: assert the payload scales with groups, not atoms.

Related: `scene_contracts.md` Contract S1, `strips.md`.
