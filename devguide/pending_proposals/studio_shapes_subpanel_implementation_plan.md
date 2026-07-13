# Studio subpanel — Shapes (implementation plan)

**Status:** implemented, pending audit (2026-07-13). Companion to
[the spec](studio_shapes_subpanel.md) and
[the UI design](studio_shapes_subpanel_ui_design.md).

**This document owns the seam.** The most repeated defect of the rework was a field
that crossed Python → controller → panel and got dropped at an intermediate mapping,
with nothing failing.

Prerequisites: **Phase 0** (T, S0 — including the six methods `ShapesManager` is
missing), **Phase 1** (S5 — `export_state` finally has a `shapes` key), **Phase 2**
(S1 — the authoritative summary). This panel is **Phase 7**.

---

## 1. The summary op

`set_shape_summaries`, via **`_send_runtime_only`**. Built on `shapes.info()`, which
is already almost exactly the record needed.

### The summary must be re-sent on `ready` — or the panel is empty in the popup

A summary is sent with `_send_runtime_only`, so it **never enters
`_message_history`** and a frontend that attaches later never receives it by replay.
The `ready` handler re-sends them explicitly (`core.py:789-790`), and **the new
`_sync_shape_summaries_runtime()` must be added there**.

Forget it and the panel renders **empty** — while the canvas shows the objects
happily — in the popup window, in a re-attached widget, after a kernel rebuild, and
in the standalone host. It will look perfect in the notebook it was written in and be
broken everywhere else.

## 2. The record, field by field

| field | Python | TS | source | why the panel needs it |
|---|---|---|---|---|
| `tag` | `str` | `string` | `info()['tag']` | identity — **domain-local** (T) |
| `kind` | `str` | `string` | `info()['kind']` | **decides which controls exist** |
| `op` | `str` | `string` | the wire op of the record | the mutator matrix keys off **the op**, not the pretty kind |
| `hidden` | `bool` | `boolean` | `not info()['visible']` | the eye |
| `layer_tag` | `str \| None` | `string \| null` | `info()['layer_tag']` | `· layer:` — omit when degenerate (S4) |
| `color` | `str \| None` | `string \| null` | `info()['color']` | the swatch (spheres) |
| `n_colors` | `int \| None` | `number \| null` | `len(options['colors'])` | `colours (12)` for per-element kinds |
| `radius` | `float \| None` | `number \| null` | `info()['radius']`, **magnitude** | the number |
| `n_radii` | `int \| None` | `number \| null` | `len(options['radii'])` | `radii (12)` |
| `alpha` | `float \| None` | `number \| null` | `options['alpha']` | the slider's **current** value |
| `radius_scale` / `length_scale` | `float \| None` | `number \| null` | `options[…]` | the sliders' current values |
| `unit` | `str` | `string` | `"angstrom"` | rendering `1.5 Å` |
| `atom_indices` | `list[int]` | `number[]` | derived | focus |

**`op` is the field the panel cannot work without, and `info()` does not return it.**
The mutator matrix (spec §2.2) is keyed on the **wire op** (`add_sphere`,
`add_network_links`, …), not on the display kind. Ship the op, or the panel will have
to reverse-map the kind string back to an op — a second mapping that will drift from
the first.

**`alpha`, `radius_scale` and `length_scale` are not in `info()` either.** They live
in `options` of the shape record. Without them the sliders **do not know their own
current value** and would snap to a default the moment the user touches them —
silently overwriting the user's styling. This is exactly the seam defect this document
exists to prevent.

So `shapes.info()` must be **extended** in this phase (or the summary reads the record
directly — but then two projections exist and will drift; extend `info()`).

## 3. Render status: a diagnostic, **not** scene state

`render_status()` is **runtime-only by design** (its own docstring: *"not part of the
reproducible scene history used for rebuilds or exports"*).

Therefore it **must not travel in the Python summary.** It is reported by the frontend
while trajectory-bound shapes resolve, so the panel reads it **locally**, in the
frontend, and it updates as the frame changes without any Python round-trip.

Contract S1 governs **scene state**. Runtime diagnostics are not scene state, and
routing them through Python would put a message on every frame — the toll this repo has
already paid once.

## 4. The actions

New members of the closed `PanelAction` union, each with a handler in the
`interaction_context_action` dispatcher in `core.py`.

| action | payload | Python call (post-Phase-0 manager) |
|---|---|---|
| `toggle_shape_visibility` | `{tag}` | `shapes.show(tag)` / `.hide(tag)` — **new in Phase 0** |
| `rename_shape` | `{tag, new_tag}` | `shapes.set_tag(...)` — **new in Phase 0** |
| `set_shape_layer` | `{tag, layer\|null}` | `shapes.set_layer_tag(...)` |
| `set_shape_color` | `{tag, color}` | `Shape.set_color` (spheres) / `set_colors` (per-element, all to one) |
| `set_shape_alpha` | `{tag, alpha}` | `Shape.set_alpha` |
| `set_shape_radius` | `{tag, radius}` | `Shape.set_radius` / `set_radii` |
| `set_shape_scale` | `{tag, kind, value}` | `Shape.set_radius_scale` / `set_length_scale` |
| `show_all_shapes` / `hide_all_shapes` | `—` | loop |
| `clear_shapes` | `—` | `shapes.clear()` |

**Already exists, reuse:** `delete_shape` (`core.py:1429`).

**The one to remove:** the visibility toggle at `viewer-controller.ts:2958`
(`handleMessage({op: "hide_layer"})`). It becomes `toggle_shape_visibility`. **That
deletion is the Contract S2 fix** — and note it is only *possible* because Phase 0
gives `ShapesManager` a `hide()` at all. The API gap and the architectural defect were
the same wound.

**Python must validate against the matrix**, not just the panel. A handler that
receives `set_shape_color` for a `channel-tube` must do the right thing (route to
`set_colors`) or refuse cleanly — never let `NotImplementedError` escape to the user
as a broken panel.

## 5. Units: the magnitude **and** the unit, in both directions

Radii are lengths, and a bare number is not a length.

**The rule: the unit makes the round trip. The panel never chooses one.**

```jsonc
// summary → panel
{ "radius": { "magnitude": 1.5, "unit": "angstrom" } }

// panel → Python (the SAME unit it was handed)
{ "action": "set_shape_radius", "tag": "site1",
  "radius": { "magnitude": 2.0, "unit": "angstrom" } }
```

A slider that returns a **bare `2.0`** forces the Python handler to *guess* the unit. It
would guess right today — everything is normalised to ångström on creation
(`spheres.py:143`) — and it would guess wrong the day someone changes that, scaling every
sphere by ten with nothing raising. **The panel echoes back the unit it received**, so
there is no guess to get wrong.

*(For the record: a bare float would not silently mis-scale today — `puw.get_value(1.5,
to_unit="angstroms")` raises `NotImplementedFormError`, and `Shape.set_radius` carries
`@digest`. The unit system already refuses bare numbers, on purpose. But relying on an
exception to catch a design ambiguity is not a design; carry the unit.)*

Do **not** stringify a `puw` quantity and parse it in TS — that is a second unit system
in the frontend, and it will drift. Python owns the quantity; the wire carries a
magnitude and its unit; the panel formats.

## 6. Files

| file | change |
|---|---|
| `molsysviewer/shapes/__init__.py` | extend `info()` with `op`, `alpha`, scales, `n_colors`, `n_radii` |
| `molsysviewer/viewer/…` | `_shape_summary_records()` + `_sync_shape_summaries_runtime()` |
| `molsysviewer/viewer/core.py` | the new handlers, with matrix validation |
| `js/src/ui/panels/shapes-panel.ts` | **new**; owns the kind → controls matrix |
| `js/src/ui/panels/types.ts` | the new `PanelAction` members |
| `js/src/ui/group-panel.ts` | mount it; `setShapeSummaries()` |
| `js/src/managers/viewer-controller.ts` | consume the summary; **delete** `addonsShapes`; keep `render_status` local |
| `js/src/ui/panels/inspector-list-panel.ts` | **delete** — this is the last of its three users |
| `molsysviewer/viewer.js` | **generated** — rebuild last. Never hand-edited. |

## 7. Tests

Every mechanism verified by **mutation**.

**Python**
- The summary carries `op`, `alpha` and the scales, **with their real values** — not
  `isinstance(dict)`.
- `shapes.hide(tag)` (new) works, and the summary reflects it.
- **A shape round-trips** through `export_state`/`import_state` **with its colour and
  radius**. *(Today there is no `shapes` key at all — §0.3. This is the test that
  proves Phase 1 landed.)*
- Every action refuses cleanly on a kind that does not support it. **`NotImplementedError`
  must never reach the user.**

**JS unit**
- **The matrix**: for each kind, exactly the supported controls render. A kind with no
  mutators renders the "no editable style" sentence. *Table-driven — one case per row
  of the matrix.*
- Every affordance dispatches a `panel_action`; assert **no** `handleMessage` for a
  state mutation.

**E2E, real browser** (the Phase 14 harness)
- Hiding a shape from the panel removes it from the **Mol\* render tree** *and* Python
  reports it hidden. This is the defect that shipped, and no unit test proves both
  halves at once.
- Changing a sphere's colour from the panel changes it in the render tree.

## 8. Implementation record (2026-07-13)

Implemented for audit:

- `ShapesPanel` replaces the last `InspectorListPanel` user. It manages existing
  shapes only; there is no GUI creation path.
- The authoritative summary is projected from `shapes.info()`, carries the wire
  `op`, real style values, explicit angstrom units and broken-anchor state, and is
  re-sent on ready and after shape style mutations.
- Render status remains frontend-local for the panel and runtime-only for Python.
  It is absent from summaries, exported state and scene history.
- Every lifecycle and style affordance crosses the closed `PanelAction` seam. The
  backend validates the capability matrix before calling a shape mutator.
- Continuous style controls use scene-history coalescing. Radius edits echo the
  exact unit received from Python.
- The real-browser E2E covers a no-mutator shape, colour, visibility, deletion and
  undo against both Python state and the Mol* render tree.

Observed validation:

- Python: 738 collected, 3 skipped, exit 0.
- JavaScript unit tests: 187 passed, 0 failed.
- TypeScript: `npx tsc --noEmit`, exit 0.
- Real-browser E2E: 21 suites passed, including `shapes-subpanel.e2e.ts`.
- Runtime bundle: regenerated with `npm run build:runtime` after all source and test
  changes.

Auto-mutation record:

| mechanism | temporary mutation | guarding test | observed result |
|---|---|---|---|
| frontend capability matrix | offer `color` for displacement vectors | `ShapesPanel derives exactly the editable controls from every wire op` | failed mutated; passed restored |
| backend capability matrix | claim `set_colors` for `add_pocket_surface` | `test_shape_panel_capability_matrix_only_exposes_working_mutators` | failed with `NotImplementedError`; passed restored |
| explicit radius units | emit the stored nanometer value instead of the angstrom wire quantity | `test_shape_summary_carries_real_style_values_and_explicit_angstrom_unit` | failed mutated; passed restored |
| runtime-only diagnostics | add `shape_render_status` to exported state | `test_shape_render_status_is_runtime_only_and_queryable` | failed mutated; passed restored |

Deliberately not implemented in this phase: shape creation from the GUI, custom
shape authoring, and new mutators for the four wire ops that currently expose no
editable style. These remain the explicit out-of-scope items from the spec.
