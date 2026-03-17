# Interaction Overview

This page is the entrypoint for the interaction and picking design of
MolSysViewer.

It is the working contract for canvas interaction.
It should guide implementation order, payload design, and API decisions.

## Purpose

MolSysViewer should not behave only as a renderer.
It should behave as an inspection workbench for structural biology,
biochemistry, and drug design.

That means canvas interaction must support at least:

- inspection,
- stable selection,
- context-aware actions,
- measurement workflows,
- and future Python callbacks.

## Core Interaction Invariants

These invariants should remain true unless a later design explicitly changes them:

- hover is not persistent selection
- focus is not selection
- selection does not imply automatic focus
- tool-mode picks should not overwrite general working selection by default
- interaction payloads should stay useful in notebook contexts without requiring a heavy UI layer

## Current State

Already implemented:

- JS -> Python interaction events for:
  - `interaction_hover`
  - `interaction_click`
  - `interaction_context_menu`
  - `interaction_context_action`
  - `interaction_active_selection_changed`
  - `interaction_tool_state`
  - `interaction_measurement_created`
- Python stores the last observed event for each of those families
- viewer-owned context menu in the canvas
- left-click selection and `Shift` additive selection
- empty-click clear semantics
- `left drag` rotate and `right drag` pan preserved
- double-left-click focus
- explicit measurement tool modes:
  - `distance`
  - `angle`
  - `dihedral`
- visible tool-status overlay with progress and `Esc` hint
- first real `active_selection` runtime slices for:
  - `element`
  - `annotation`
  - `shape`
  - narrow `mixed`
- first `GroupStrip` runtime slice synchronized with canvas interaction
- first annotation runtime slice with persistent labels
- first reproducible UI -> Python bridges for:
  - selection -> region
  - selection -> label
  - interactive measurement -> persisted measurement artifact

Important implementation gap to keep visible:

- the runtime is now meaningfully group-centric for element selection, but the
  full public Python object model around `active_selection`, `hover_target`,
  `context_target`, and `tool_selection` is still not finalized
- mixed-selection semantics are real but still intentionally narrow
- several UX paths are deliberately minimal first slices rather than final UI
  design, especially label-text capture

## Design Pages

1. [**Targets and Selection**](interaction_targets_and_selection.md)
   - Target taxonomy, picking levels, `active_selection`, mixed selection, and group-pick metadata.
2. [**Gestures and Menus**](interaction_gestures_and_menus.md)
   - Hover/click/double-click semantics, context menus, and measurement/tool modes.
3. [**Modifiers and Future**](interaction_modifiers_and_future.md)
   - Reserved modifiers, future ideas, borrowed design principles, and deferred questions.

## Closed Enough for Implementation

- target taxonomy: `empty`, `element`, `shape`, `annotation`
- public term `group`
- default group-centric picking policy
- measurement/tool modes force atom-level picking
- `active_selection` is a public object
- mixed selection is allowed from the beginning
- left click replaces selection
- `Shift + left click` adds to selection
- left click on empty clears selection
- `left drag` rotates
- `right drag` translates/pans
- right click without drag opens menu without changing active selection
- right click sets `context_target`
- double left click focuses

## Immediate Implementation Guidance

When implementation resumes, proceed under the reproducibility-first rule:

1. strengthen the Python-facing object model for interaction state
2. keep converting exploratory interaction into explicit replay-safe state
3. improve weak UX slices only after their reproducible contract is stable
4. then add richer interaction polish such as level choosers, tooltips, and
   broader mixed-selection behavior

## Non-Goals for the First Implementation Pass

Do not try to solve all of these immediately:

- full menu UX polish
- fully general mixed-selection operations
- shape-specific contextual operations for every overlay family
- popup synchronization of interaction state
- advanced multi-step editing tools beyond the current measurement scaffolding
- final polished text-entry UX for labels

The first goal is a stable and well-specified interaction contract.

## Tool Lifecycle and Cancellation

Any multi-step interaction (measurements, multi-pick tools) must follow these rules:

- **Visual Feedback**: A persistent status banner or overlay must be visible while a tool is active, showing:
  - the current tool name (e.g., "Distance Measurement"),
  - progress (e.g., "Pick 1 of 2"),
  - and instructions for cancellation.
- **Escape Key**: The `Esc` key is the universal cancellation signal. Pressing `Esc` must:
  - immediately terminate the current tool mode,
  - clear any partial picks,
  - and restore the default interaction state (camera controls and group selection).
- **Cursor State**: Optionally, the mouse cursor should change to indicate a "picking" state when a tool is active.

## Callback Direction

Python-side callbacks are still part of the intended interaction surface, but
they are not yet a stabilized public callback API.

Working callback names to keep visible during design and implementation:

- `on_hover`
- `on_click`
- `on_context_menu`
- `on_tool_pick`

These are placeholders, not final API commitments.
