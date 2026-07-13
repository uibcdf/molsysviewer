# Studio subpanel — Layers (implementation plan)

**Status:** proposed (2026-07-12). Companion to
[the spec](studio_layers_subpanel.md) and
[the UI design](studio_layers_subpanel_ui_design.md).

**This document owns the seam.**

Prerequisites: **Phase 0** (`LayersManager` with `.add()`, `provenance`, identity),
**Phase 1** (S5 — `provenance` and the layers serialise), **Phase 2** (S1 — the
summaries). This panel is **Phase 8**, and it goes last **because it consumes every
other domain's summary**.

---

## 1. The summary: this panel is a *join*, not a domain

Layers has no records of its own worth pushing separately — a layer *is* its
membership. It is assembled from:

- `set_region_summaries` — which already carries `layer` (Phase 9 of the rework);
- `set_shape_summaries`, `set_annotation_summaries`, `set_measurement_summaries` —
  each carrying `layer_tag`;
- plus a new **`set_layer_summaries`** for what belongs to the layer *itself* and to
  nothing else: `tag`, **`provenance`**, `hidden`.

**Without `set_layer_summaries` an empty user layer cannot exist on screen** — it has
no members to be inferred from. That is the whole point of Contract S4b, and it is the
field the naive implementation will forget.

### The summary must be re-sent on `ready` — or the panel is empty in the popup

A summary is sent with `_send_runtime_only`, so it **never enters
`_message_history`** and a frontend that attaches later never receives it by replay.
The `ready` handler re-sends them explicitly (`core.py:789-790`), and **the new
`_sync_layer_summaries_runtime()` must be added there**.

Forget it and the panel renders **empty** — while the canvas shows the objects
happily — in the popup window, in a re-attached widget, after a kernel rebuild, and
in the standalone host. It will look perfect in the notebook it was written in and be
broken everywhere else.

## 2. The layer record

| field | Python | TS | why |
|---|---|---|---|
| `tag` | `str` | `string` | identity |
| `provenance` | `"auto" \| "user"` | `"auto" \| "user"` | **the panel shows only `user`** |
| `hidden` | `bool` | `boolean` | the group eye |
| `member_count` | `int` | `number` | the card, and the empty state |

Members are **not** duplicated into this record: they are joined in the frontend from
the other four summaries, keyed by `(kind, tag)` — **not by tag alone** (Contract T:
`site1` may be a region *and* a shape).

**The trap:** `buildLayers()` today groups by any non-empty `layerTag`, which is why
loose objects show up as one-member groups. The join must filter on the layer's
`provenance`, which means it needs `set_layer_summaries` to know it at all.

## 3. The actions

| action | payload | Python call |
|---|---|---|
| `create_layer` | `{tag}` | `layers.add(tag)` — **new in Phase 0** |
| `rename_layer` | `{tag, new_tag}` | `Layer.set_tag(...)` |
| `ungroup_layer` | `{tag}` | detach every member, drop the layer — **objects survive** |
| `delete_layer_and_contents` | `{tag}` | `Layer.delete()` (deletes members) |
| `add_member_to_layer` | `{layer, member_tag, member_kind}` | **branches on kind** (§4) |
| `remove_member_from_layer` | `{layer, member_tag, member_kind}` | **branches on kind** (§4) |
| `set_layer_visibility` | `{tag, hidden}` | `Layer.show()` / `.hide()` — **already exists** (`core.py:1205`) |

**`delete_layer_group` (`core.py:1220`) is today the only destructive action, and it
calls `Layer.delete()`, which deletes the members.** Split it: `ungroup_layer` becomes
the safe default, and the destructive one is renamed to say what it does. Leaving one
action that silently deletes the user's regions and shapes is a data-loss bug wearing
an icon.

## 4. `member_kind` is load-bearing — the seam's whole point

Membership has **two channels** (Contract S4):

```python
# scene objects
obj.set_layer_tag(layer)      #  Shape / Annotation / Measurement
Layer.detach(obj)

# regions  — DIFFERENT FIELD
region.set_layer(layer)       #  region.layer, NOT region.layer_tag
region.remove_from_layer()
```

Code that walks `Layer.members` and writes `member.layer_tag` **silently orphans every
region in the layer** — which is exactly what a layer rename used to do in this repo
(`architecture.md` §Key invariants 2).

So the action payload **must carry `member_kind`**, and Python **must branch on it**.
Inferring the kind from the tag is not an option: under Contract T a region and a shape
may share a tag.

**Mutation test, mandatory:** put a region and a shape *with the same tag* in a layer;
detach the shape; **assert the region is still in the layer** and still knows it. If
that test passes with the branch removed, it is hollow.

## 5. Files

| file | change |
|---|---|
| `molsysviewer/layers.py` | `provenance`; `Layer.ungroup()`; promotion rules |
| `molsysviewer/viewer/scene_registry.py` | auto-cleanup **only for `provenance == "auto"`** |
| `molsysviewer/viewer/…` | `_layer_summary_records()` + `_sync_layer_summaries_runtime()` |
| `molsysviewer/viewer/core.py` | the new handlers; split the destructive action |
| `js/src/ui/panels/layers-panel.ts` | rewrite: member picker, kind-aware detach, `provenance` filter |
| `js/src/ui/panels/types.ts` | the new `PanelAction` members |
| `js/src/managers/viewer-controller.ts` | join the five summaries; **`setLayerObjects` disappears** — it was fed by the shadow maps |
| `molsysviewer/viewer.js` | **generated** — rebuild last. Never hand-edited. |

## 6. Tests

Every mechanism verified by **mutation**.

**Python**
- **An empty user layer survives** being emptied, and survives a **round-trip**.
  *(Mutate: drop `provenance` from the serialisation → the layer is reborn `auto` and
  evaporates. That test is the one that protects S4b.)*
- An `auto` layer **is** still cleaned up when empty (the other half — a test that only
  checks persistence would pass with the cleanup deleted entirely).
- **Promotion**: adding a second member to an `auto` layer makes it `user` — including
  when the second member is a **region** (the `region.layer` channel).
- `ungroup_layer` keeps the objects; `delete_layer_and_contents` does not.

**JS unit**
- Only `provenance == "user"` layers render, and the badge counts only those. *(Today
  three loose spheres render as three groups.)*
- The member picker offers only members not already in the layer.
- Detach dispatches the correct `member_kind`.

**E2E, real browser**
- Hiding a layer hides **all** its members in the Mol\* render tree — regions **and**
  scene objects — and Python agrees on every one of them.
