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

## Current State

Already implemented:

- minimal JS -> Python event bridge for:
  - `interaction_hover`
  - `interaction_click`
- atom-centric transport for the first slice:
  - structure picks emit `atom_indices`
  - empty canvas emits `kind: "empty"`
- Python stores:
  - `get_last_hover_event()`
  - `get_last_click_event()`

This is only the transport baseline.
It is not yet the full interaction contract.

## Design Pages

1. [**Targets and Selection**](interaction_targets_and_selection.md)
   - Target taxonomy, picking levels, `active_selection`, mixed selection, and group-pick metadata.
2. [**Gestures and Menus**](interaction_gestures_and_menus.md)
   - Hover/click/double-click semantics, context menus, and measurement/tool modes.
3. [**Modifiers and Future**](interaction_modifiers_and_future.md)
   - Reserved modifiers, future ideas, borrowed design principles, and deferred questions.

## Closed Enough for Implementation

- target taxonomy: `empty`, `structure`, `shape`
- public term `group`
- default group-centric picking policy
- measurement/tool modes force atom-level picking
- `active_selection` is a public object
- mixed selection is allowed from the beginning
- left click replaces selection
- `Shift + left click` adds to selection
- left click on empty clears selection
- right click opens menu without changing active selection
- right click sets `context_target`
- double left click focuses

## Immediate Implementation Guidance

When implementation resumes, proceed in this order:

1. enrich the interaction payload so it can represent structural targets at `group` level and not only raw atom lists
2. define a first stable Python-facing representation for `active_selection`
3. implement left-click selection replacement/add semantics
4. implement empty-click clear semantics
5. add right-click `context_target` and menu-launch event semantics
6. implement tool-mode scaffolding for measurement workflows
7. only after that, add richer UI polish such as temporary level choosers or hover tooltips

## Non-Goals for the First Implementation Pass

Do not try to solve all of these immediately:

- full menu UX polish
- every modifier binding
- fully general mixed-selection operations
- shape-specific contextual operations for every overlay family
- popup synchronization of interaction state
- advanced multi-step editing tools beyond measurement scaffolding

The first goal is a stable and well-specified interaction contract.
