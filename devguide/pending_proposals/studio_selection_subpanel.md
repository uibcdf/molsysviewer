# Proposal: Studio → Selection subpanel (native selection management)

**Status:** pending (design agreed; not implemented).

**Scope:** the **Selection** subpanel of the **Studio** panel in MolSysViewer.
Gives the user adequate and complete control over the viewer's *native* selection
management. It intentionally overlaps with the MolSysMT add-on's future
`Basic → Selection`; the five surfaces and their boundaries are laid out in §7. The
add-on side is postponed.

This document supersedes and folds in an earlier collaborator draft
(`studio_selection_panel_proposal.md`); what was adopted / changed is noted in §9.

---

## 1. Why

### 1.1 The taxonomy already exists; the UI underuses it

MolSysViewer already models selection as three distinct things
(`devguide/selections.md`):

- **`active_selection`** — transient interaction state: what the user is currently
  working with.
- **`selection`** — a persistent, *named* capture of a working set, with **no**
  automatic scene representation.
- **`region`** — a persistent structural object *with* scene meaning (representation,
  visibility).

Intended progression: *explore interactively → obtain an active selection → persist
it as a named selection → optionally promote it to a region / annotation / analysis
input*.

The Python surface backing this is rich and already implemented (verified in code):

- `view.active_selection`: `set(selection | indices, *, syntax)`, `atom_indices`,
  `group_indices`, `component_indices`, `molecule_indices`, `chain_indices`,
  `entity_indices`, `source_kind`, `element_level`, `target_level`, `focus(...)`,
  `save(tag)`, `clear()`, `new_region(...)`, `add_label(...)`, `info()`, `is_empty()`.
- `view.selections`: `add(tag, *, atom_indices, items)`,
  `add_selection(tag, selection, *, element, mask, syntax)`,
  `add_from_active_selection(tag)`, `activate(tag)`, `tags`, `contains`, `get`,
  `records`, `count`, `info`, `set_tag` (rename), `delete`, `clear`; per-selection
  wrapper `info/activate/focus/new_region/add_label/set_tag`.
  **Note:** `add_selection` *resolves* the expression to atom indices via
  `view.select` and stores only those (`_store_selection_record` keeps
  `atom_indices` + per-level indices + `element_level`, but **no expression /
  syntax**). Persistence is index-based today — see §5.
- `view.select(selection, *, structure_indices, element, mask, syntax)` → indices,
  in the current-system index space (`MolSysMTInterfaceMixin`).

The **current** subpanel exposes only a fraction: it shows the active selection's
atom count + level with `Clear / Save / Create Region`, and a flat list of saved
selections (activate on click, delete on hover). The gap between the model and the
UI is the opportunity.

### 1.2 What "complete control" means

A molecular viewer's native selection management should let a user:

1. **Build** a working set — by interaction *and* by query, refined with set
   operations (union / subtract / intersect / invert), at any structural level.
2. **Inspect** it — count, composition, defining level.
3. **Persist & manage** named selections — save, rename, re-activate, delete,
   compose.
4. **Promote** a selection into other viewer categories — region, annotation label.
5. Stay **reproducible** across rebuild / export.

Today only (2)–(3, partial) are covered. This proposal completes (1)–(5).

### 1.3 Foundations: two base sources, five surfaces

Selection in the ecosystem rests on **two base sources**:

- **Managing** selections → the **molsysviewer public API**
  (`view.active_selection`, `view.selections`, the operations, activation,
  persistence). The **authority** over the shared selection state and its lifecycle.
- **Making** selections → the **MolSysMT selection API** (the selection language;
  `msm.select`: expression → indices). The **engine** of creation. `view.select` is
  the viewer's thin adapter: it delegates the *making* to MolSysMT and returns
  indices in the current-system index space.

On top of those bases there are **five selection-management surfaces**, each with its
own flavour and peculiarities. They **do not constrain one another**, but they
**share one philosophy** and route to the same two bases:

1. The **molsysviewer public API** (also the management base itself).
2. The **Studio → Selection subpanel** (GUI) — *this proposal*.
3. The **`Basic → Selection` subsection** of the MolSysMT add-on panel (GUI).
4. The **`molsysviewer_molsysmt` add-on public API** (programmatic).
5. The **mouse over the canvas / 3D structure** plus **right-click and its context
   menu** (direct manipulation).

All five write the **same** `active_selection` and create via the **same** MolSysMT
engine. This subpanel (#2) is one surface, not a separate selection engine.

**Shared philosophy — invariants every surface honours:**

- a single shared `active_selection` state;
- *making* goes through the MolSysMT selection language (one grammar);
- *managing* goes through the molsysviewer public API (authority for named
  selections and operations);
- one common **set-operation vocabulary** (Replace / Add / Subtract / Intersect /
  Invert) that means the same everywhere;
- best-effort **reproducibility** across rebuild / export;
- **no persistent operation "mode"** that silently governs later actions on the
  shared selection — the operation is chosen *at the moment of acting* (see §3).

**Flavour — free to differ per surface:** exact gestures / shortcuts, widget layout,
amount of guidance (chips, cheat-sheet), and whether operations are offered as
immediate buttons, keyboard modifiers, or a **sticky-for-one-action** control (all of
which are compliant, because none is a *persistent* mode).

---

## 2. What (scope)

**In scope (this subpanel):**

- **Inspection** of the shared `active_selection`, and applying the set-operation
  vocabulary to it through the subpanel's **own** controls (query box + buttons).
  Canvas / strips gestures are peer surfaces, not owned here (§3.2).
- MolSysMT-syntax **query box** plus guided, viewer-friendly affordances.
- Hierarchical **expansion** to whole groups / components / molecules / chains /
  entities (the five supra-atomic levels; `atom` is the identity).
- Named-selection persistence and management (save / rename / activate / delete /
  compose).
- **Promote** bridges: → Region, → 3D annotation label.
- Reproducibility (store the defining expression where one exists).

**Out of scope (placed elsewhere, to be studied):**

- **Visibility actions** (Isolate / Hide / Show-only) — belong to the Visibility
  model, not selection management.
- **Focus / zoom-to-selection** — a camera action; deferred (the API supports
  `active_selection.focus()`, but placement is TBD).
- **Add-on `Basic → Selection`** — postponed; §7 lays out the five surfaces.

---

## 3. Interaction model — one shared state, several input surfaces

Per §1.3, `active_selection` is one shared state and this subpanel is one of the five
surfaces onto it. Its state and contract are owned by
`interaction_targets_and_selection.md`, **not** by this proposal. This section fixes
how the *subpanel* applies the shared vocabulary and how it relates to the peer
surfaces.

### 3.1 Shared operation vocabulary (cross-cutting — not owned here)

The set operations any surface applies to `active_selection` are
**Replace · Add · Subtract · Intersect · Invert** (plus All / None). This vocabulary
is cross-cutting; it belongs to the `active_selection` contract, not to any one
surface. Today the contract defines only **Replace / Add-toggle / Range**
(`interaction_targets_and_selection.md`; `Shift`+click *toggles* — it removes an
already-selected element, so per-item de-selection already exists).
**Subtract and Intersect are a pending extension of that contract** and are recorded
there (see §8), so every surface shares one definition.

**The narrow invariant** (§1.3): no surface arms a *persistent* operation mode that
silently governs later actions on the shared `active_selection`; the operation is
chosen at the moment of acting. The reason is that a mode governs a **shared** target:
a surface-local armed mode would not carry to the canvas or add-on (so it confuses),
and a global armed mode would fight the canvas's built-in `Shift`=Add and force every
surface to display/respect it — both worse than choosing the operation per action.
Non-persistent affordances — immediate buttons, keyboard modifiers, or a
**sticky-for-one-action** control — are all compliant flavour choices.

### 3.2 Canvas & strips — peer surfaces (referenced, not defined here)

Their gesture bindings live in `interaction_targets_and_selection.md` /
`interaction_modifiers_and_future.md` and are **unchanged by this proposal**: plain
click = Replace, `Shift`+click = Add/toggle, `Shift`+`Alt`+click = Range, click on
empty = Clear. Because `Shift`+click already toggles, per-item subtraction on the
canvas needs no new modifier (and `Alt`+click is avoided anyway — Linux window
managers commonly capture it). Surface #5 also includes **right-click and its context
menu**; its selection actions (e.g. select residue / add to selection / expand / save
selection) apply the same shared vocabulary and live with the interaction /
context-menu spec, not here.

### 3.3 How this subpanel exposes the vocabulary (owned here)

The subpanel presents the operations as **explicit, immediate controls** on its own
inputs — never a global mode:

| Subpanel input | Replace | Add | Subtract | Intersect |
|----------------|---------|-----|----------|-----------|
| Query box | `Select` | `+ Union` | `− Subtract` | `∩ Intersect` |
| Saved-selection row | click row | `+` | `−` | `∩` |

Plus `All / None / Invert` in the active-selection toolbar (§4A). Group-level
Subtract / Intersect (e.g. "subtract all HIS", "intersect with a saved selection")
cannot be expressed by a single canvas click — which is exactly why they belong on
these buttons. A small **modifier legend** near the strips reminds users of the
shared click gestures, whose authority remains the interaction docs. (If bulk
building warrants it, a **sticky-for-one-action** variant of these buttons is a
compliant addition — it arms an op for the next single action then reverts, so it is
not a persistent mode.)

---

## 4. Design — subpanel layout

Vertical stack inside the Studio → Selection content area. Pure selection
management; no visibility controls.

### A. Active Selection card

- **Quick toolbar:** `All · None · Invert` (global set ops on the current system).
- **Stats:** `N atoms · N groups · N chains · <level>` (from `active_selection`
  level getters). Empty state: "No active selection."
- **Expand to whole:** `group · component · molecule · chain · entity` — for each
  selected atom, include all atoms sharing that element. (Terminology is MolSysMT's:
  **group**, not "residue".) Backed by the level index getters.
- **Persist:** `Save as…` (inline name → a **named selection**; the tag/name lives
  here).
- **Promote bridges:** `→ Region`, `→ Label (3D)` — create a region or a 3D
  annotation from the active selection. (These are bridges into other categories;
  kept here as a "promote" affordance, symmetric with each other.)

### B. Select by query

- **Input** + **syntax dropdown** (`MolSysMT` | `Indices`).
- **Operation buttons:** `Select` (Replace) · `+ Union` · `− Subtract` ·
  `∩ Intersect` — apply the resolved query to the active selection with that op.
- **Guided chips** (insert exact syntax into the box, teaching by example):
  `protein` → `molecule_type=="protein"`, `water`, `backbone`, `sidechain`,
  `ligand`, and a **`within X Å of selection`** helper. NOTE: distance is **native
  `select` syntax** (`"… within <X> angstroms of …"`), *not* a contacts computation.
- **Cheat-sheet** `[?]`: collapsible card with common examples (by atom name, group,
  chain, molecule_type, `within`, `bonded to`).
- **Validation on apply:** the expression is validated by sending it to
  `view.select`; a `NotSupportedSyntaxError` is surfaced inline (no client-side
  grammar parser — see §6.3).

### C. Saved Selections manager

- List rows sorted by tag: `name · N atoms · <level>`.
- Click row = **activate (Replace)**. Per-row compose buttons `+ / − / ∩`.
- Per-row menu: `Activate · Rename · → Region · → Label · Delete`.
- Empty: "No saved selections yet."

---

## 5. Reproducibility model

A Selection carries **both**:

- its **resolved indices** (molecular-system index space), and
- its **provenance** — when it was produced by a query, the `(expression, syntax,
  element)` triple; when produced by interaction, just the indices.

**This is new work, not reuse.** The current persistence layer is **index-only**:
`_store_selection_record` (and the `save_selection` message it sends) has no
expression/syntax field, and `add_selection` throws the expression away after
resolving it. Making query-based selections reproducible therefore requires
**extending** the record + `save_selection` op + `Selection` wrapper to carry the
optional `(expression, syntax, element)` provenance. Do not assume it is already
stored.

Replay behaviour (target):

- **Query-based** selections re-evaluate from the (newly stored) expression — fully
  reproducible across rebuild / topology change.
- **Interaction-based** selections replay by **remapping indices** via
  `atom_index_map` during `apply_system_edit` rebuilds (the mechanism the viewer
  already uses to survive edits).
- **Composed** selections (a sequence of query/interaction ops) store an ordered
  **recipe** of operations; best-effort replay re-applies it. The simple, common
  case (one named query selection) is fully reproducible once provenance is stored.

"Live / dynamic" selections (re-evaluate per trajectory frame) are **deferred**;
default is *frozen indices + stored expression*.

---

## 6. Architecture / How

### 6.1 Frontend (`molsysviewer/js/src/ui/group-panel.ts`)

`renderSelectionSection()` is extended from its current two blocks (Active + Saved)
to the A/B/C layout above. Reuse existing helpers (`makeSectionHeader`,
`makeRowElement`, `makeButton`) and the existing interaction plumbing:

- Clicks already flow through `onSelect(items, additive)` →
  `ActiveSelectionController.setItems(items, additive, isRange)`, and the additive
  branch already **toggles** (removes an already-selected element). So clicks need
  **no change** for the interaction model: Replace / `Shift`=Add-toggle /
  `Shift`+`Alt`=Range are all in place. Group-level Subtract/Intersect are handled
  in the panel buttons, not in the click path.
- New panel actions route through the existing `onAction(action, details)` channel
  (today it carries `save_selection`, `create_region_from_selection`,
  `delete_selection`). Add: `apply_selection_query`, `expand_selection`,
  `invert_selection` / `select_all` / `select_none`, `rename_selection`,
  `compose_saved_selection`, `create_label_from_selection`.

### 6.2 Backend (`molsysviewer/viewer/core.py` frontend-event handlers)

New ops resolve on the Python side so provenance is known there:

- `apply_selection_query {expression, syntax, op}`: the active selection is
  atom-based, so resolve at atom level — `new = view.select(expression,
  syntax=syntax)` for `syntax="MolSysMT"`, or pass the raw index list straight to
  `active_selection.set(...)` for `syntax="Indices"` (bypassing `view.select`).
  Combine with `view.active_selection.atom_indices` per `op`
  (replace/union/subtract/intersect); `view.active_selection.set(result)`; record
  `(expression, syntax, op)` in the active selection's provenance recipe. Errors →
  inline message, no state change. (Note: MolSysMT's `element` level is *not* a query
  parameter here — it belongs to the Expand feature below, which promotes the
  atom-level active selection to whole groups/chains/etc.)
- `expand_selection {level}`: use the active selection's `<level>_indices` getter to
  re-`set` at that level.
- `invert_selection`: `all` minus current (`view.molsys.get_n_atoms()`); `select_all`
  / `select_none` analogous.
- `rename_selection {tag, new_tag}` → `view.selections[tag].set_tag(new_tag)`.
- `compose_saved_selection {tag, op}` → combine `view.selections[tag]` indices with
  active per `op`.
- `create_label_from_selection {tag?}` → `view.active_selection.add_label(...)`.
- Existing: `save_selection` → `active_selection.save(tag)`;
  `create_region_from_selection` → `new_region_from_active_selection`;
  activate saved → `selections.activate(tag)`; `delete_selection`.
  For §5, `save_selection` / `_store_selection_record` / the `Selection` record must
  gain an optional `(expression, syntax)` provenance field (index-only today).

Each op echoes the new active-selection payload back to the frontend
(`set_active_selection`) so strips/3D stay in sync.

### 6.3 Autocompletion (feasibility-driven, tiered)

Full grammar-aware autocomplete is **rejected** for now: the MolSysMT selection
grammar (attributes, `in [...]`, `within/of`, `bonded to`, `and/or/not`,
parentheses) would have to be re-implemented in TypeScript and would drift from the
Python source. Instead:

1. **Keyword/attribute typeahead** — static vocabulary
   (`atom_name, group_name, group_index, chain_name, molecule_type, component_index,
   entity_name, within, of, in, and, or, not, bonded to`).
2. **System-value suggestions** — from the loaded Mol* structure: after
   `group_name in` suggest residue names present; after `chain_name ==` the chains
   present. High value, feasible client-side.
3. **Chips + cheat-sheet** as the guided fallback (§4B).
4. **Apply-time validation** via `view.select` error surfacing (no client parser).

If true autocomplete is wanted later, expose a molsysmt-side `suggest/complete`
endpoint so the grammar stays single-sourced in Python.

---

## 7. The five surfaces and where this one sits

There are **five** selection-management surfaces over the two base sources (§1.3).
Overlap is acceptable; each has its own flavour and none constrains the others, but
all share the philosophy and route to the same bases.

| # | Surface | Kind | Flavour |
|---|---------|------|---------|
| 1 | molsysviewer public API | programmatic (base for *managing*) | the authority; everything else routes through it |
| 2 | **Studio → Selection subpanel** *(this proposal)* | GUI | interaction-native, fast/visual; builds & refines the working set, manages named selections, promotes into viewer categories (regions, annotations) |
| 3 | add-on `Basic → Selection` subsection | GUI | scientific; richer domain queries, history logs, code export — may be *less* viewer-friendly (TBD) |
| 4 | `molsysviewer_molsysmt` add-on public API | programmatic | selections as input to analysis (contacts, hbonds, …) |
| 5 | canvas mouse + right-click context menu | direct manipulation | pick / range / toggle on the 3D and strips; context actions |

- **This panel (#2)** speaks the *scene* vocabulary and is the home for named-selection
  management and the promote bridges.
- **The add-on (#3, #4)** speaks the *analysis* vocabulary; its GUI flavour and how
  viewer-friendly it is are **postponed**.
- **Integration (future, postponed):** all surfaces operate on the **same**
  `view.selections` registry and the same `active_selection`, so a selection made in
  any surface is visible/usable in the others — no parallel worlds.

---

## 8. Deferred / open

- **Extend the shared `active_selection` contract** with **Subtract / Intersect** in
  `interaction_targets_and_selection.md` (they exist in the vocabulary but the
  contract only defines Replace/Add-toggle/Range). This is cross-cutting, not owned
  by this subpanel; recorded there so all surfaces share one definition.
- **Focus / zoom-to-selection** placement (camera action).
- **Visibility bridges** (Isolate / Hide) — Visibility-model panel.
- **Live/dynamic** (per-frame re-evaluated) selections.
- **Add-on side** design and the shared-registry integration.

---

## 9. Provenance (what was merged from the collaborator draft)

Adopted from `studio_selection_panel_proposal.md`: the sectioned card layout (here
adapted to A/B/C), the guided **chips**, the **cheat-sheet / self-documentation**
strategy, explicit **boolean operation buttons**, per-row saved-selection compose
(`+ / − / ∩`), and the Studio/add-on boundary idea (here expanded to the five
surfaces of §7).

Changed / corrected:

- **Distance** is native `select` syntax (`within … of …`), **not**
  `msm.structure.get_contacts`; it is a query, not a separate spatial-compute
  "expander".
- **Expansion to all five** supra-atomic levels (`group, component, molecule, chain,
  entity`) — the draft had three — using MolSysMT's level vocabulary (**group**, not
  "residue").
- **Reproducibility** (store the expression) added — the draft collapsed everything
  to index sets.
- **Interaction model** unified with the existing canvas modifier idiom instead of
  living only on the query box; no global mode.
- **Autocompletion** scoped to a feasible tiered plan (the draft assumed full
  autocomplete + validation without addressing grammar cost).
- Scope trimmed to **selection management**; visibility/focus explicitly deferred.

## 10. Suggested implementation slices

1. Query box + operation buttons + apply-time validation (biggest capability gain).
2. Modifier legend near the strips (clicks already support Replace / `Shift`=Add-
   toggle / `Shift`+`Alt`=Range — no click-path code change).
3. Expand-to-level row (all six).
4. Saved-selection manager upgrade (rename, compose, promote menu).
5. Guided chips + cheat-sheet.
6. Reproducibility (provenance recipe + expression persistence).
