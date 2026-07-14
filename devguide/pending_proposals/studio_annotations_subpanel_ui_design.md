# Studio subpanel — Annotations (UI design)

**Status:** implemented (2026-07-14). Companion to
[the live spec](studio_annotations_subpanel.md).

Visual language: the existing Studio panels. Reuse `makeSectionHeader`,
`makeSettingsCard`, `makeButton`, `makeRowElement` from `panels/ui-helpers.ts`. **No
new design system** — indistinguishable in style from Regions and Whole.

---

## 1. The one-line brief

> The scientist opens Annotations to **read and correct what they wrote**.

So the **text is the row**, and editing it must be one click away. Today it is
impossible without deleting and recreating the annotation.

---

## 2. Layout

```
┌─ Annotations ─────────────────────────────── [3] ─┐
│                                                    │
│  ┌ New annotation ────────────────────────────┐    │
│  │  [ Catalytic triad_______________ ]        │    │
│  │  Anchored to the active selection (3 atoms)│    │
│  │  [ Add ]                                    │   │
│  └────────────────────────────────────────────┘    │
│                                                    │
│  Annotations                                       │
│  ┌────────────────────────────────────────────┐    │
│  │  Catalytic triad              [👁] [⋯] [🗑] │    │
│  │  annotation1 · 3 atoms                     │    │
│  └────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────┐    │
│  │  [ Gate closed______________ ] [✓] [✗]     │    │  ← editing in place
│  │  annotation2 · 1 atom · layer: gate        │    │
│  └────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────┐    │
│  │  ⚠ Mutation site              [👁] [⋯] [🗑] │    │
│  │  annotation3 · anchor broken               │    │
│  └────────────────────────────────────────────┘    │
│                                                    │
│  [ Show all ]  [ Hide all ]  [ Clear all ]         │
│                                                    │
│  ┌ Style ─────────────────────────────────────┐    │
│  │  Colour [#ffffff]   Size [1.0 em]          │    │
│  │  ☑ Background      Opacity [0.6]           │    │
│  └────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────┘
```

## 3. The row

1. **The text.** Primary, prominent — it *is* the annotation. Clicking it (or the
   `⋯` → Rename) turns it into an **inline input** with confirm/cancel, in the same
   pattern the Selection panel already uses for saved selections
   (`data-molsysviewer-saved-selection-confirm`). Enter confirms, Escape cancels,
   blur confirms.
   - This is the feature of the panel. It must not be buried in a submenu.
2. **Identity.** `annotation1 · 3 atoms`, plus `· layer: gate` when it belongs to a
   **user** layer. The degenerate auto-layer is never shown (Contract S4).
3. **Broken anchor** (Contract S7): a **⚠ marker** and `anchor broken` in place of
   the atom count. The text stays visible — the user wrote it and it is still
   meaningful — but nothing renders and no stale position is implied.

Actions: **eye**, **⋯** (rename tag, move to layer, re-anchor to active selection),
**🗑**. All dispatch a `panel_action`; none touches the runtime directly (S2).

A hidden row dims to ~42% opacity, as Regions does.

## 4. Creating an annotation

A text box plus **Add**, anchored to the **active selection**, stating what it will
anchor to (*"3 atoms"*). If the selection is empty, the button is disabled **with
the reason written out** — *"Select atoms to anchor the annotation"* — never a
mutely greyed button.

Note the anchor is the **centroid** of the atoms, and the active selection is held
at group level (`canvas_picking_level.md` §0), so an atom-level pick may come back
snapped to its residue. Say the atom count; do not pretend it is what the user
clicked.

**No `kind` selector.** Only `"label"` exists. A dropdown with one option is noise.

## 5. The style card

`label_style` is Python-only today: `color`, `size_em`, `background`,
`background_opacity`. Surface it as a card at the bottom.

**One decision to make explicit:** is the style **per annotation** or a **panel-wide
default**? The API takes it **per annotation** (`add_annotation(label_style=…)`), so
the card must act on the **selected row**, and read its current values — not be a
global setting pretending to be one. If no row is selected, the card sets the
default for the *next* annotation, and says so in one line.

Getting this wrong produces the worst kind of control: one that looks global and
acts local.

## 6. Empty and error states

- **No annotations:** *"No annotations yet. Select atoms, type a text and press
  Add."* — the empty state points at the action.
- **No system loaded:** the creation card is disabled with *"Load a structure
  first."*
- **Broken anchor:** the row survives with its ⚠. It is never silently dropped: the
  user wrote it, and an annotation vanishing on its own is worse than one that
  admits it is broken.

## 7. The badge

The annotation count, kept in sync from the summary (`ctx.setBadge`).
