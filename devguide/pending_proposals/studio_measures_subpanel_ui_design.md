# Studio subpanel — Measures (UI design)

**Status:** proposed (2026-07-12). Companion to
[the spec](studio_measures_subpanel.md) and
[the implementation plan](studio_measures_subpanel_implementation_plan.md).

Visual language: the existing Studio panels. Reuse `makeSectionHeader`,
`makeSettingsCard`, `makeButton`, `makeRowElement` from
`panels/ui-helpers.ts`. **No new design system** — this panel should be
indistinguishable in style from Regions and Whole.

---

## 1. The one-line brief

> The scientist opens Measures to **read numbers**. Everything else is secondary.

So the number is the largest, highest-contrast element in a row. The tag is
metadata. Today the row shows the tag and hides the number; that is exactly
backwards.

---

## 2. Layout

```
┌─ Measures ────────────────────────────────── [3] ─┐
│                                                    │
│  ┌ New measurement ───────────────────────────┐    │
│  │  From active selection (6 atoms)           │    │
│  │  [ Distance ] [ Angle ] [ Dihedral ]       │    │
│  │  Needs 2 picks · you have 1                │    │
│  └────────────────────────────────────────────┘    │
│                                                    │
│  Measurements                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  5.93 Å                       [👁] [⋯] [🗑] │    │
│  │  distance · d1                             │    │
│  │  N (res 1)  →  C (res 2)                   │    │
│  │  ▁▂▃▅▆▅▃▂▁▂▃  (series, 500 frames)         │    │
│  └────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────┐    │
│  │  112.4°                       [👁] [⋯] [🗑] │    │
│  │  angle · a1 · layer: site                  │    │
│  │  CA → CB → CG                              │    │
│  └────────────────────────────────────────────┘    │
│                                                    │
│  [ Show all ]  [ Hide all ]  [ Clear all ]         │
│                                                    │
│  ┌ Endpoint policy ───────────────────────────┐    │
│  │  ( ) Atom   (•) Centroid   ( ) Representative│   │
│  │  Representative atoms:                     │    │
│  │    protein [CA]  nucleic [P]               │    │
│  │    lipid   [P ]  other   [  ]              │    │
│  └────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────┘
```

## 3. The row

The unit of this panel. Four bands, top to bottom:

1. **The value.** `5.93 Å`, `112.4°`. Large, bold, primary colour. This is the
   product. Formatting: distances to 2 decimals, angles to 1 — driven by the
   `puw` quantity, never by a hand-rolled unit string.
   - When the value cannot be resolved: `—`, muted, with the reason on hover.
     A measurement whose atoms vanished after a system edit must not render a
     stale number.
2. **Identity.** `distance · d1`, plus `· layer: site` when it belongs to a
   user layer. Small, muted. (The degenerate auto-layer is **not** shown —
   Contract S4.)
3. **The endpoints.** `N (res 1) → C (res 2)`, from `endpoint_labels`. This is
   what tells the user *what they measured*, and it is the second most valuable
   thing on the row after the number.
4. **The series**, only when the system has a trajectory and the measurement has
   more than one stored value: a **sparkline** over the frames, with the current
   frame marked. Clicking it is out of scope for this slice; reading it is not.

Actions, right-aligned: **eye** (show/hide), **⋯** (rename, move to layer), **🗑**
(delete). All three dispatch a `panel_action` — never a direct runtime call
(Contract S2).

A hidden row dims to ~42% opacity, as Regions does.

## 4. Creating a measurement

The gesture the panel is missing entirely today. The card reads the **active
selection** and offers the three kinds, enabling only the one that fits:

- `Distance` needs 2 picks, `Angle` 3, `Dihedral` 4.
- The card states what it has and what it needs — *"Needs 2 picks · you have
  1"* — rather than silently disabling the buttons. A disabled button with no
  explanation is the worst of both worlds.

**What is a "pick"?** Not an atom: an *endpoint*, which may be a group of atoms
reduced by the endpoint policy. The active selection is held at **group level**
(`canvas_picking_level.md` §0 — a Python-set selection of two atoms comes back as
the whole residue), so the panel must reason in endpoints, not in atom counts,
or the arithmetic will look wrong to the user.

For this slice, the composition of endpoints from successive canvas picks is out
of scope: the card creates a measurement from the **current** selection, and the
canvas tool mode remains the way to build multi-pick measurements interactively.

## 5. The endpoint policy card

Global to the domain, not per measurement — so it sits at the bottom, below the
list, and reads as a setting rather than an action.

- The three policies as radio buttons (`atom`, `centroid`, `representative_atom`
  — default `centroid`).
- The four representative atoms as small text inputs (`protein: CA`,
  `nucleic: P`, `lipid: P`, `other: ""`), enabled **only** when the policy is
  `representative_atom`. Showing them always, greyed, teaches what the policy
  means; hiding them would make the policy opaque.
- Changing the policy affects **future** measurements (the API sets a default);
  it does **not** retroactively recompute existing ones. The card must say so in
  one line, or the user will assume it does — this is the kind of silent
  mismatch that erodes trust in a number.

## 6. Empty and error states

- **No measurements:** *"No measurements yet. Select atoms and choose a kind
  above."* — the empty state points at the action, it does not merely state the
  absence.
- **No system loaded:** the creation card is disabled with *"Load a structure
  first."*
- **A measurement that cannot resolve:** the row survives, showing `—`. It is
  never silently dropped: the user created it, and a measurement disappearing on
  its own is worse than one that admits it is broken.

## 7. The badge

The tab badge is the measurement count, kept in sync from the summary — the same
mechanism every migrated panel uses (`ctx.setBadge`).
