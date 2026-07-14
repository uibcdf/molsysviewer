# Studio subpanel — Annotations (spec)

**Status:** implemented (2026-07-14). This spec and the
[UI design](studio_annotations_subpanel_ui_design.md) describe the live panel.
References to "today" below describe the audited pre-implementation baseline.

**Normative:** [`scene_contracts.md`](../scene_contracts.md). This spec **points at** the
contracts; it never restates their rules. (The Whole spec of the rework went stale
precisely by copying normative semantics that later changed.)

---

## 1. What this panel is for

An annotation says *what something is*. It is the layer of meaning the scientist
adds on top of the structure: **"catalytic triad"**, **"gate closed"**, **"mutation
site"**.

Today the panel lists them and lets you focus, hide and delete. **It cannot edit
the text** — the single most obvious thing a user wants to do with a label — even
though `annotations.set_text()` has existed all along.

## 2. What the domain offers (`molsysviewer/annotations.py`)

**Creation.** `add_annotation(text, kind="label", selection=…, atom_indices=…, tag,
layer_tag, syntax="MolSysMT", label_style=…)`.

- **`kind` currently accepts only `"label"`.** It is a forward-looking parameter;
  the panel must not present a choice that does not exist.
- **`add_label()` is deprecated** — it warns and delegates. The panel must be built
  on `add_annotation`.
- `add_label_from_active_selection(...)` exists and is the GUI-native gesture.

**The anchor.** The annotation is anchored to a set of atoms, and its position is
their **centroid**. `set_anchor(...)` and `set_group_index(...)` re-anchor it.
`Annotation.set_coordinates()` raises `NotImplementedError` on purpose: an anchor is
atoms, not a free position.

**Editing.** `set_text(tag, text)` — edits **in place**, no delete-and-recreate.

**Style.** `label_style` accepts `color` (CSS hex), `size_em` (float),
`background` (bool), `background_opacity` (0–1). **None of it is reachable from the
GUI today.**

**Reading.** `info(tag=None)` → `kind`, `tag`, `layer_tag`, `text`, `n_atoms`,
`atom_indices`, `visible`, `active`.

**Lifecycle.** `show`, `hide`, `delete`, `clear`, `set_tag`, `set_layer_tag`,
`contains`, `get`, `count`, `records`, `tags()`.

> ⚠️ `tags` is a **property** here and a **method** in measurements and shapes — so
> `view.annotations.tags()` raises `TypeError`. Phase 0 (Contract S0) makes it a
> method everywhere. Build against the post-Phase-0 API.

## 3. How an annotation is drawn

By **Mol\*'s `label` representation** with `customText`
(`js/src/managers/handlers/annotation-handlers.ts`) — not by our shapes. Per
Contract V that is its `renderer="native"`, and **it stays**.

Mol\* has a far richer annotation system (MolViewSpec: free-anchored labels,
`group_id`, data-driven tooltips and colouring). It is **deliberately deferred to
post-1.0** — see [`post_1.0/annotations_mvs_machinery.md`](post_1.0/annotations_mvs_machinery.md).
Nothing this panel needs requires it.

## 4. Scope

**In:**

- **Edit the text in place** — the headline of this panel.
- Create from the **active selection**.
- The anchor: how many atoms, and re-anchoring.
- **`label_style`**: colour, size, background — today Python-only.
- Lifecycle: rename, layer, show/hide, delete, clear.
- The **broken-anchor** state (Contract S7): an annotation whose atoms vanished in
  an `apply_system_edit` shows a warning, never a stale label.

**Out:**

- **The MVS machinery** (post-1.0, above).
- **A `kind` selector** — only `"label"` exists. Do not build a dropdown with one
  entry.
- Free-positioned annotations (no atoms): the anchor is atoms by design today. The
  *anchor must stay an extensible concept* (Contract S7 / post-1.0), but this slice
  does not add the capability.

## 5. What "done" means

- The user can rename an annotation's **text** without deleting it.
- Every affordance goes through Python (Contract S2): hiding from the panel makes
  `view.annotations.info(tag)['visible']` false. Today it stays true.
- Deleting from the panel is **undoable** (Contract S6).
- Text, style, visibility and layer survive a save/reload (Contract S5) — and after
  the reload the annotation is still **manageable**, not a zombie (§0.8).
