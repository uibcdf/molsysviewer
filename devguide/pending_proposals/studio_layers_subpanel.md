# Studio subpanel — Layers (spec)

**Status:** proposed (2026-07-12). One of three: this **spec**, the
[UI design](studio_layers_subpanel_ui_design.md) and the
[implementation plan](studio_layers_subpanel_implementation_plan.md).

**Normative:** [`scene_objects_contracts.md`](scene_objects_contracts.md) — in
particular **Contract S4** (two membership channels) and **S4b** (a layer is an
entity, with `provenance`).

---

## 1. What this panel is for

A layer is the user's own **organisation of the scene**: *"everything about the
binding site"* — the region, the sphere that marks it, the distance that measures it,
the label that names it — grouped under one name, shown and hidden together.

It is the only panel whose subject is **the user's structure of thought**, not a
molecular object. That is why it must be the most forgiving of the four.

## 2. The state of it today

This is the only one of the four that already **goes through Python** correctly
(`set_layer_visibility` → `layer.hide()`, `core.py:1205`). Its problems are of a
different kind:

- **It assigns a region to a layer by typing both tags into two text boxes.**
- **Its "Remove" button is disabled for scene objects, with a tooltip that is
  false**: *"Scene objects are managed by their own addon layer tags."* They are not.
  `Layer.detach(obj)` exists and works.
- **It shows the degenerate auto-layers as if they were groups.** Every loose object
  carries `layer_tag == tag`, and `buildLayers()` groups by any non-empty layer tag —
  so three unrelated spheres render as three one-member "Layer Groups", counted in the
  tab badge.
- **There is no way to create a layer, rename it, or delete the group without
  deleting its contents.**

## 3. What Phase 0 changes underneath it

The panel cannot be fixed without the domain being fixed first:

- **`LayersManager` is new.** Layers is the only domain with no manager at all
  (`view.layers` returns the raw registry, `core.py:1706`). It gains the canonical
  surface and **`.add(tag)`** — the house verb (Contract S0).
- **`view.new_layer()` is retired** in favour of `view.layers.add()`. It is the last
  survivor of the pre-Phase-13 style that `view.new_region()` already left behind.
- **`Layer.provenance = "auto" | "user"`** (Contract S4b) — the mechanism that lets a
  user layer survive empty while the degenerate auto-layers keep being cleaned up.

## 4. The two traps

### 4.1 Membership has two channels, and it bites

**Scene objects** carry membership in **`obj.layer_tag`**. **Regions** carry it in
**`region.layer`** (Contract S4).

Any code that walks `Layer.members` and writes `member.layer_tag` **silently orphans
every region in the layer** — which is exactly what a layer rename used to do in this
repo. The panel must branch on which channel each member actually uses:

- regions → `region.set_layer()` / `remove_from_layer()`
- scene objects → `obj.set_layer_tag()` / `Layer.detach(obj)`

### 4.2 An empty layer is legal at birth and illegal when emptied

Verified 2026-07-12: `view.new_layer(tag='empty1')` **persists**; but put one member
in a layer, take it out, and the layer is **deleted** (`scene_registry.py:80-81`).

So a user creates a layer, drags its only member out to reorganise, and **the layer
evaporates**. `provenance` (S4b) is what fixes this: only `auto` layers are cleaned up
when empty.

## 5. Scope

**In:**

- **Create** a layer (`layers.add`), **rename** it (`Layer.set_tag`), **delete** it.
- **Assign and detach members** — both kinds, respecting §4.1.
- Group **visibility** (`Layer.show/hide`), and per-member state.
- **Hide the degenerate auto-layers.** A group is a *user-made* grouping.
- Two distinct destructive actions, named honestly (§6).

**Out:**

- **Nested layers.** The model is flat by design (`architecture.md` §Key invariants
  5). Do not imply a tree.
- **Layer-level colour.** Tempting, and it would collide head-on with Contract B
  (colour is layered and owned, with a single `order` per region). Out of scope until
  someone reconciles the two models on purpose.

## 6. The trash button means two different things — offer both

`Layer.delete()` today **deletes its members**. For a user layer, the thing the user
usually wants is *delete the group, keep the objects*.

Both are legitimate and they are **not** the same action:

- **Ungroup** — dissolve the layer, detach the members, they survive on their own.
- **Delete contents** — remove the layer *and* everything in it.

Presenting one trash icon that silently does the second is a data-loss bug waiting to
happen. Name both, and make the destructive one say what it will destroy.

## 7. What "done" means

- A user can create an empty layer, name it, drag things into it later, and **it is
  still there** after emptying it and after a reload (`provenance` serialises).
- Assigning a region to a layer does **not** orphan it (§4.1) — mutation-tested.
- The panel shows **only user layers**; the badge counts only those.
- No affordance can destroy the user's objects without saying so.
