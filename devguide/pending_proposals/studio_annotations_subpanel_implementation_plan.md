# Studio subpanel — Annotations (implementation plan)

**Status:** implemented; pending audit (2026-07-13). Companion to
[the spec](studio_annotations_subpanel.md) and
[the UI design](studio_annotations_subpanel_ui_design.md).

**This document owns the seam.** The most repeated defect of the scene rework was a
field that crossed Python → controller → panel and got **dropped at one of the
intermediate mappings**, with nothing failing — the panel just rendered a blank. So
the seam is specified here field by field, and the brief derives from it.

Prerequisites, all landed: **Phase 0** (T, S0 — identity, `TagsManager`s, the manager
surface), **Phase 1** (S5 — the restore path rebuilds the model), **Phase 2** (S1 —
the authoritative summary). This panel is **Phase 6**.

---

## 1. The summary op

`set_annotation_summaries`, sent with **`_send_runtime_only`** (a summary is a
projection of state, not a command: it must never enter `_message_history` or it
corrupts the replay). One op per domain — never a combined lump (Contract S1).

Built **on `annotations.info()`**, which already returns almost exactly this record.
One projection, not two: two projections of the same state will drift.

### The summary must be re-sent on `ready` — or the panel is empty in the popup

A summary is sent with `_send_runtime_only`, so it **never enters
`_message_history`** and a frontend that attaches later never receives it by replay.
The `ready` handler re-sends them explicitly (`core.py:789-790`), and **the new
`_sync_annotation_summaries_runtime()` must be added there**.

Forget it and the panel renders **empty** — while the canvas shows the objects
happily — in the popup window, in a re-attached widget, after a kernel rebuild, and
in the standalone host. It will look perfect in the notebook it was written in and be
broken everywhere else.

## 2. The record, field by field

| field | Python | TS | source | why the panel needs it |
|---|---|---|---|---|
| `tag` | `str` | `string` | `info()['tag']` | identity — **domain-local** (Contract T) |
| `text` | `str` | `string` | `info()['text']` | **the row** |
| `kind` | `str` | `string` | `info()['kind']` | always `"label"` today; carried, not shown |
| `hidden` | `bool` | `boolean` | `not info()['visible']` | the eye, the dimming |
| `layer_tag` | `str \| None` | `string \| null` | `info()['layer_tag']` | `· layer: gate` — **omit when degenerate** (S4) |
| `n_atoms` | `int` | `number` | `info()['n_atoms']` | `· 3 atoms` |
| `atom_indices` | `list[int]` | `number[]` | `info()['atom_indices']` | focus |
| `style` | `dict \| None` | `LabelStyle \| null` | the record's `options['style']` | the style card must **read** current values, not just write |
| `anchor` | `dict` | `{type, ...}` | `{"type": "atoms", "indices": [...]}` (Phase 1 format) | the anchor **is a typed object**, not a flat list — post-1.0 brings `position` and `residue` kinds |
| `broken` | `bool` | `boolean` | Contract S7 | the ⚠ row |
| `broken_reason` | `str \| None` | `string \| null` | Contract S7 | the tooltip |

The domain-level payload also carries `active_selection_count` and
`system_loaded`. The former is consumed as a fallback when a newly attached
frontend receives the summary before the live active-selection event.

**`style` is the field most likely to be lost.** It lives in
`options['style']` of the creation record, not in `info()` — which means `info()`
must be **extended** to surface it, or the panel's style card will read blanks and
silently overwrite the user's styling with defaults on first use. That is exactly
the class of seam defect this document exists to prevent.

**`broken` / `broken_reason` are new state** (Contract S7). They must reach the
summary **and** `export_state`.

## 3. The actions

New members of the closed `PanelAction` union (`js/src/ui/panels/types.ts:19`), each
with a handler in the `event == "interaction_context_action"` dispatcher in
`viewer/core.py` — the seam every panel action already uses
(`viewer-controller.ts:1023`).

| action | payload | Python call |
|---|---|---|
| `create_annotation` | `{text, label_style}` | `annotations.add_label_from_active_selection(...)` |
| `set_annotation_text` | `{tag, text}` | `annotations.set_text(tag, text)` |
| `toggle_annotation_visibility` | `{tag}` | `annotations.show(tag)` / `.hide(tag)` |
| `rename_annotation` | `{tag, new_tag}` | `annotations.set_tag(tag, new_tag)` |
| `set_annotation_layer` | `{tag, layer\|null}` | `annotations.set_layer_tag(...)` |
| `reanchor_annotation` | `{tag}` | `annotations.set_anchor(tag, <active selection>)` |
| `set_annotation_style` | `{tag, style}` | `annotations.set_style(...)` |
| `show_all_annotations` / `hide_all_annotations` | `—` | `annotations.show_all()` / `.hide_all()` |
| `clear_annotations` | `—` | `annotations.clear()` |

**Already exists, reuse:** `delete_annotation` (`core.py:1424`) already goes through
Python correctly. Focus stays a local camera move.

**The one to remove:** the visibility toggle at `viewer-controller.ts:2910`, which
calls `handleMessage({op: "hide_layer"})` directly and leaves Python's `_hidden`
stale. It becomes `toggle_annotation_visibility`. That deletion **is** the Contract
S2 fix for this domain.

`annotations.set_style()` had already landed before this phase. The panel uses it
directly; it never recreates a label to restyle it.

## 4. Text editing: coalesce, do not spam the history

Editing text fires a mutation per keystroke if wired naively, and the undo stack is
bounded at 25 (`scene_history.py:45`) — so typing one word would **evict the user's
entire history** (Contract S6).

Record the undo on **blur or Enter**, never per keystroke, and open the coalescing
window in the **history**, not in the panel (a Python loop must be protected too).

## 5. Files

| file | change |
|---|---|
| `molsysviewer/annotations.py` | surface `style` in `info()`; a style mutator if missing |
| `molsysviewer/viewer/…` | `_annotation_summary_records()` + `_sync_annotation_summaries_runtime()` |
| `molsysviewer/viewer/panel_actions/scene_objects.py` | the new `interaction_context_action` handlers |
| `js/src/ui/panels/annotations-panel.ts` | **new** — replaces `InspectorListPanel` for this tab |
| `js/src/ui/panels/types.ts` | the new `PanelAction` members |
| `js/src/ui/group-panel.ts` | mount it; `setAnnotationSummaries()` |
| `js/src/managers/viewer-controller.ts` | consume the complete typed summary and route it to the panel |
| `molsysviewer/viewer.js` | **generated** — `npm run build:runtime` as the **last** step. Never hand-edited. |

## 6. Tests

Every mechanism verified by **mutation**: revert it, its test must fail.

**Python**
- `set_text` from the panel action changes the text **and** the summary, and
  survives a round-trip.
- Hiding from the panel makes `info(tag)['visible']` false. *(Today it stays true —
  that is the §0.2 mutation.)*
- `style` survives creation → summary → `export_state` → `import_state`. **Assert the
  values**, not that the key exists.
- **Contract S7**: delete the anchor atoms via `apply_system_edit`; the annotation comes
  back **`broken`, with its reason — not silently deleted**. *(Today it vanishes
  entirely: `info()` returns `[]`. Measured, §0.10.)*

**JS unit**
- The row renders the text; the inline editor confirms on Enter and cancels on
  Escape.
- Every affordance dispatches its `panel_action`. Assert **no** `handleMessage` is
  called for a state mutation — that assertion is the regression guard for the defect
  this phase removes.

**E2E, real browser** (the Phase 14 harness)
- Hiding an annotation from the panel removes its label from the **Mol\* render
  tree** *and* Python reports it hidden. No unit test proves both halves at once, and
  this is exactly the defect that shipped.

## 7. Implementation record (2026-07-13)

- `AnnotationsPanel` replaces the generic inspector and owns creation, inline
  text editing, lifecycle controls, re-anchoring and per-label/default style.
- Text, color and sliders bracket continuous edits with the scene-history
  coalescing events. Programmatic loops use the same `view.history.coalescing()`
  mechanism.
- The Python summary is authoritative for style, typed anchor, atom count,
  visibility and broken state. All mutations go through panel actions; focus is
  the only local camera operation.
- `annotations-subpanel.e2e.ts` uses Python-generated messages and then inspects
  Mol\*'s real `customText` and tagged render refs.

Auto-mutation record:

| mechanism | mutation | protecting test | observed result |
|---|---|---|---|
| history coalescing deduplicates repeated `set_text` | force `already_coalesced = False` | `test_typing_a_label_does_not_wipe_the_undo_history` | fails: 17 undo entries instead of 4; passes restored |
| style action rejects a non-mapping | remove the `Mapping` guard | `test_annotation_panel_actions_reject_invalid_style_or_empty_reanchor` | style case fails; passes restored |
| re-anchor rejects an empty active selection at the panel seam | remove the early empty-selection guard | same parametrized test | re-anchor case fails on the changed error contract; passes restored |
| inline editing opens a history window | make `beginCoalescing()` a no-op | `GroupPanel Annotations edits labels and routes every mutation through panel actions` | JS bundle test fails; passes restored |

Validation observed on the final source tree:

- Python suite: exit 0, 100% collected tests completed, 3 skipped.
- JavaScript unit suite: 183 passed, 0 failed.
- `npx tsc --noEmit`: exit 0, no errors.
- Browser/WebGL: 20/20 E2E suites passed, including the new annotations
  subpanel and the migrated broken-anchor and Python round-trip checks.
- `npm run build:runtime`: exit 0; `viewer.js` regenerated from TypeScript.
