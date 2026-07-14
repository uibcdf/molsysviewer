# Studio subpanel — Layers (UI design)

**Status:** implemented (2026-07-14). Companion to
[the live spec](studio_layers_subpanel.md).

Visual language: the existing Studio panels (`panels/ui-helpers.ts`). No new design
system.

---

## 1. The one-line brief

> Layers is where the user **organises the scene into their own ideas**.

It is the only panel whose subject is the user's structure of thought rather than a
molecular object. So it must be forgiving: nothing here should destroy work by
accident, and nothing should vanish on its own.

---

## 2. Layout

```
┌─ Layers ──────────────────────────────────── [2] ─┐
│                                                    │
│  ┌ New layer ─────────────────────────────────┐    │
│  │  [ binding site______________ ]  [ Create ]│    │
│  └────────────────────────────────────────────┘    │
│                                                    │
│  ┌ binding site ──────────────── [👁] [⋯] ────┐    │
│  │  2 regions · 3 objects                     │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │ pocket        region · 128 atoms  [-]│  │    │
│  │  │ ligand        region · 44 atoms   [-]│  │    │
│  │  │ site1         shape · sphere      [-]│  │    │
│  │  │ d1            measurement         [-]│  │    │
│  │  │ note1         annotation          [-]│  │    │
│  │  └──────────────────────────────────────┘  │    │
│  │  Add member:  [ tag ▾ ]          [ Add ]   │    │
│  └────────────────────────────────────────────┘    │
│                                                    │
│  ┌ gate ──────────────────────── [👁] [⋯] ────┐    │
│  │  empty — drop something in                 │    │
│  │  Add member:  [ tag ▾ ]          [ Add ]   │    │
│  └────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────┘
```

## 3. Creating a layer

A name and a **Create** button. That is all. **An empty layer is legal and it stays**
(Contract S4b) — its card shows *"empty — drop something in"* rather than disappearing.

This is the single most visible fix in this panel: today a layer that loses its last
member **evaporates**, so a user reorganising their scene watches their groups vanish.

## 4. Adding a member: a picker, not two text boxes

Today the panel assigns a region by **typing both tags into two text inputs**. Replace
it with a **picker of existing members** (a `<select>` of the scene's regions, shapes,
measurements and annotations that are not already in this layer), scoped to the card
of the layer it will join.

The user should never have to remember and retype a tag that the panel already knows.

**Group the picker by domain** (`<optgroup>`). A scene with eighty objects makes a flat
list unusable, and the domain is exactly the axis the user thinks along:

```
┌ Add member ──────────────────┐
│  ── Regions ──               │
│     pocket        128 atoms  │
│     ligand         44 atoms  │
│  ── Shapes ──                │
│     site1         sphere     │
│  ── Measures ──              │
│     d1            distance   │
│  ── Annotations ──           │
│     note1         "gate"     │
└──────────────────────────────┘
```

This is not cosmetic: under Contract T **a region and a shape may share a tag**, so a
flat list would show `site1` twice with no way to tell them apart. The domain heading
*is* the disambiguator — and it is the same `member_kind` the action must carry
(implementation plan §4).

## 5. Members: show the kind, and act on the right channel

Each member row shows **tag · kind** (`pocket · region · 128 atoms`, `d1 ·
measurement`). The kind is not decoration — it decides which API detaches it:

- regions → `region.remove_from_layer()`
- scene objects → `Layer.detach(obj)`

Writing the wrong field **silently orphans the member** (Contract S4). Today the panel
sidesteps this by **disabling "Remove" for scene objects with a tooltip that is
false** (*"Scene objects are managed by their own addon layer tags"*). They are not:
`detach()` exists. Enable it, and route it correctly.

## 6. Only user layers are shown

A loose object carries `layer_tag == tag` — its own degenerate auto-layer. Today
`buildLayers()` groups by any non-empty layer tag, so **three unrelated spheres render
as three one-member "Layer Groups"**, counted in the badge.

Filter on `provenance == "user"` (Contract S4b). A group is a **user-made** grouping.
The auto-layers stay in the model, where they are load-bearing; they simply are not
groups and must not be shown as such.

## 7. Two destructive actions, both named

The `⋯` menu offers **Rename**, and then two clearly separated items:

- **Ungroup** — dissolve the layer; the members survive on their own.
- **Delete layer and contents** — remove everything in it. Confirms, and **names what
  it will destroy** (*"Delete 'binding site' and its 5 objects?"*).

`Layer.delete()` today does the second **silently**. One trash icon that quietly
deletes the user's regions, shapes and measurements is a data-loss bug wearing an
icon. Never offer the destructive one as the default gesture.

## 8. Group visibility

The eye on the card header hides the whole layer (`Layer.hide()`), which cascades to
its members. A member hidden individually shows as dimmed within a visible layer —
the two states are independent and both must be legible, or the user will not
understand why something is not showing.

## 9. Empty and error states

- **No layers:** *"No layers yet. Create one to group regions, shapes, measurements
  and annotations under a single name."* — the empty state explains what a layer *is*,
  because this is the panel whose concept is least obvious.
- **An empty layer:** *"empty — drop something in"*. It does **not** disappear.

## 10. The badge

The count of **user** layers only.
