# Studio subpanel — Shapes (UI design)

**Status:** implemented (2026-07-14). Companion to
[the live spec](studio_shapes_subpanel.md).

Visual language: the existing Studio panels (`panels/ui-helpers.ts`). No new design
system.

---

## 1. The one-line brief

> The scientist opens Shapes to **restyle the figure** — and to find out **why
> something is not showing**.

Those are the two jobs. Everything else is secondary.

---

## 2. The governing constraint: controls are derived, never generic

The style mutators are **not uniform across shape types** (see the matrix in the
spec). `set_color` works only on spheres; four types support nothing at all.

So the row's controls are **computed from the shape's kind**. A control that the kind
does not support is **not rendered** — not shown-and-disabled, not shown-and-broken.
And when a kind supports nothing, the row says so plainly:

> *"This shape type has no editable style."*

That sentence is a feature. The alternative — a row of dead knobs — teaches the user
that the panel lies.

## 3. Layout

```
┌─ Shapes ──────────────────────────────────── [4] ─┐
│                                                    │
│  Shapes                                            │
│  ┌────────────────────────────────────────────┐    │
│  │  sphere · site1               [👁] [⋯] [🗑] │    │
│  │  ● #ff8800   radius 1.5 Å   alpha ▓▓▓░ 0.8 │    │
│  └────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────┐    │
│  │  channel-tube · pore          [👁] [⋯] [🗑] │    │
│  │  colours (12)   radii (12)   alpha ▓▓░░ 0.6│    │
│  └────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────┐    │
│  │ ⚠ pocket-surface · p1         [👁] [⋯] [🗑] │    │
│  │  Not rendered on frame 42                  │    │
│  │  alpha ▓▓▓░ 0.7                            │    │
│  └────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────┐    │
│  │  rings · r1                   [👁] [⋯] [🗑] │    │
│  │  This shape type has no editable style.    │    │
│  └────────────────────────────────────────────┘    │
│                                                    │
│  [ Show all ]  [ Hide all ]  [ Clear all ]         │
└────────────────────────────────────────────────────┘
```

## 4. The row

1. **Kind and tag** — `sphere · site1`. The kind first: it is what determines what
   the user can do, so it is the primary fact.
2. **The render warning** (⚠), when `render_status` reports the shape did not resolve
   on the current frame. Second line, with the cause; tooltip carries the detail.
   **This is frame-dependent** — it changes as the trajectory plays.
3. **The style controls**, derived from the kind:
   - **single colour** (spheres) — a swatch;
   - **per-element colours** (links, tubes, tetrahedra, faces, ellipsoids,
     pharmacophore) — *not* a colour picker per element. Show the count
     (`colours (12)`) and offer **set-all-to-one-colour**. Editing 12 colours
     individually is a Python job, not a panel job, and pretending otherwise
     produces an unusable row.
   - **radius** (spheres) — a number with units; **radii** (per element) — same
     treatment as colours;
   - **alpha** — a slider, on the 9 kinds that support it;
   - **scales** — `radius_scale` (displacement vectors, pocket blobs),
     `length_scale` (displacement vectors).
4. **Actions**: eye, ⋯ (rename, move to layer), 🗑.

Every slider records its undo on **release** (`dragEnd`), never per mouse-move — the
undo stack is bounded at 25 and one drag would evict the user's whole history
(Contract S6). The coalescing lives in the **history**, not here; the panel only opens
and closes the window.

## 5. Units are not decoration

Radii are lengths. They display **with units** (`1.5 Å`), and they are edited as
quantities. The Python API **rejects bare numbers on purpose**
(`ArgumentError: A length requires explicit units … to avoid silent nm/angstrom scale
errors`). The panel must not be the place where that discipline is quietly dropped —
it sends a quantity, and Python remains the authority on the unit.

## 6. No creation card

The 15 constructors take geometry — centres, vertex triples, coordinate pairs,
tetrahedra quads — that has no sane GUI. Shapes are created from Python or by an
addon; **this panel manages them**. The empty state says exactly that, instead of
offering a button that cannot exist:

> *"No shapes yet. Shapes are created from Python (`view.shapes.add_sphere(…)`) or by
> an add-on."*

## 7. Empty and error states

- **No shapes:** the message above — it teaches where shapes come from.
- **A shape that does not render:** the ⚠ row. It is never hidden or dropped: the
  user created it, and silence is the current behaviour and the bug.
- **A kind with no editable style:** stated in words, not implied by absence.

## 8. The badge

The shape count, from the summary (`ctx.setBadge`).
