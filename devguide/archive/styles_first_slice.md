# Styles: First Implementation Slice

**Status:** implemented historical plan. Do not use as current API reference.

This page defines the first concrete implementation slice for `Style` in
MolSysViewer.

It exists to bridge:

- the current runtime reality
  - `representation`
  - `preset`
  - `user_preset`
- and the broader product vision in `v1_vision_and_styles.md`

The purpose of this page is to keep the first step narrow, reproducible, and
compatible with the current architecture.

## Why A Narrow First Slice Is Necessary

The repository already has real representation mechanics.

Current code already supports:

- global representation updates through `view.whole.set_representation(...)`
- region representation updates through `region.set_representation(...)`
- built-in presets
- Python-side `user_preset` resolution
- replay/export/rebuild of those representation decisions

What does **not** exist yet is a first-class public `Style` concept.

So the next step should not try to implement the full 1.0 vision in one move.
It should:

- formalize a stable `Style` object,
- keep it serializable and replay-safe,
- and reuse the current representation machinery instead of bypassing it.

## Current Base Layer

Today the effective base layer is:

- `representation`
  - one direct representation type such as `cartoon` or `line`
- `preset`
  - one named preset such as `auto` or `polymer-cartoon`
- `user_preset`
  - a Python-defined preset bundle resolved into a JS-ready payload

This means the first `Style` slice should **wrap and clarify** that base layer,
not replace it immediately.

## First Product Decision

The first implemented `Style` should be:

- a **scene style**
- exclusive
- global-first

This means:

- it defines the baseline look of the whole scene,
- it replaces the current global representation state,
- and it maps cleanly to the existing `set_global_representation` pathway

This first slice should **not** try to solve cumulative overlays or per-target
styling logic yet.

So, for the first implementation:

- implement `Scene Style`
- defer `Focus Style`

## Why Start With Scene Style

Starting with scene style is healthier because:

- it maps directly to `view.whole`
- it already has replay/export/rebuild semantics
- it avoids immediate overlap with regions, annotations, and measurements
- it gives users a cleaner language than raw `preset`/`representation`
- it lets us validate the object model before adding compositional complexity

## Non-Goals Of The First Slice

Do **not** try to include these yet:

- cumulative focus styles
- style stacks
- automatic style algebra
- region-specific style composition rules
- chemistry-driven rule engines
- GUI style browsers
- YAML/JSON interchange as a stable user-facing format
- style inheritance graphs
- visual themes for annotations, measurements, and shapes

Those may come later.

They should not be part of the first contract.

## First Public API Proposal

The first narrow public surface should be:

- `view.styles`
- `view.styles.apply(...)`
- `view.styles.current()`
- `view.styles.info()`

And a simple value object:

- `Style`

First-path usage should be possible in two forms:

```python
view.styles.apply(preset="polymer-cartoon")
```

and

```python
style = Style(preset="polymer-cartoon")
view.styles.apply(style)
```

## Minimal `Style` Object Model

The first `Style` object should carry only what the runtime can already honor
reliably:

- `kind`
  - fixed to `"scene"` in the first slice
- one of:
  - `representation`
  - `preset`
  - `user_preset`
- optional `params`
- optional human-readable `name`

Important rule:

- for the first slice, `Style` is a Python-facing semantic wrapper over the
  already-existing representation contract

It is **not** yet a new TS-native state system.

## Validation Rules

The first slice should enforce:

- exactly one of:
  - `representation`
  - `preset`
  - `user_preset`
- `kind == "scene"` only
- `params` must remain JSON-serializable
- `Style` application must delegate to existing normalized pathways

That means:

- `Style(representation="cartoon")` is valid
- `Style(preset="auto")` is valid
- `Style(representation="cartoon", preset="auto")` is invalid

## Runtime Mapping Rule

The first implementation should map:

- `view.styles.apply(style)`

to:

- `view.whole.set_representation(...)`

with no hidden alternate state store.

This is important.

The first `Style` slice should be:

- semantic in Python,
- but operationally backed by existing representation state

That keeps:

- replay logic simple,
- rebuild behavior stable,
- export behavior unchanged,
- and user understanding cleaner.

## Persistence And Replay Contract

Applying a first-slice `Style` should remain reproducible through the already
existing representation messages.

So, in the first slice:

- no new frontend message op is required
- no parallel style-history system is required
- replay should still be driven by the existing global representation message

This is deliberate.

The first goal is **semantic clarity**, not protocol proliferation.

## Relationship With Existing API

For a transition period, both of these can coexist:

- `view.whole.set_representation(...)`
- `view.styles.apply(...)`

But the intended direction should be:

- `whole.set_representation(...)`
  - low-level explicit representation API
- `styles.apply(...)`
  - higher-level visual/scientific styling API

The first slice should not remove or deprecate the lower-level API yet.

## Interaction With Regions

The first slice should not style regions directly.

Reason:

- region representation already exists and works
- introducing scene style plus region style in the same step would blur scope

So the first rule is:

- `view.styles.apply(...)` affects the scene baseline through `view.whole`
- region styles remain a later extension

## Interaction With User Presets

`user_preset` is the most natural bridge toward the future richer style model.

So the first slice should preserve:

- current `user_preset` resolution rules
- current validation
- current replay/export behavior

And simply allow that pathway to be expressed as a `Style`.

## Usability Goal

The first user-facing benefit should be clarity, not more options.

A user should be able to understand:

- "this is the current baseline visual style of my scene"

without having to reason directly in terms of:

- representation internals
- preset normalization rules
- or frontend-specific vocabulary

## Suggested Implementation Order

1. Add a `Style` value object in Python.
2. Add `StylesManager` bound to `MolSysView`.
3. Implement `view.styles.apply(...)` by delegating to `view.whole.set_representation(...)`.
4. Add `current()` / `info()` as lightweight inspection helpers.
5. Add regression coverage.
6. Only then decide the next slice:
   - focus styles,
   - region styles,
   - or transport/export schema for shared styles.

## Minimum Test Contract

The first slice should have tests for:

- valid construction from `representation`
- valid construction from `preset`
- invalid construction when both are passed
- `view.styles.apply(...)` delegating to the same replay-safe message flow as `whole.set_representation(...)`
- `current()` reflecting the last applied scene style
- rebuild/export preserving the same outcome

## Exit Criteria

The first slice is good enough when:

- users can describe the current scene baseline as a `Style`
- the API improves clarity without increasing protocol complexity
- replay/export/rebuild behavior remains stable
- the code does not duplicate the current representation system
- the project has a real bridge from "representations and presets" to "styles"

## Operational Rule

Keep this rule visible during implementation:

> The first `Style` should clarify the current representation model, not
> replace it prematurely.
