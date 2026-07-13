# Phase 1 — The session document, field by field (state v2, extended)

**Status:** proposed (2026-07-12). Companion to
[the spec](phase1_state_restore.md) and
[the implementation plan](phase1_state_restore_implementation_plan.md).

**This document owns the format.** The subpanels have a UI design where this phase has
a wire format: the session document *is* the user-visible artefact of Phase 1, and it
is the thing that must not break.

**Normative:** Contract **C** (`scene_contracts.md`) and Contract **S5**;
[`session_reproducibility.md`](../session_reproducibility.md) is the standing rule.

---

## 1. It stays version 2 — every new key is additive

```
version, whole, regions, annotations, measurements, selections, active_selection,
order_high_water_mark, uid_high_water_mark          ← today
+ shapes            ← new
+ layers            ← new
+ tag_high_water_marks   ← new
```

A v2 reader that ignores the new keys still works, and **a v2 document written before
this phase must import cleanly** — missing `shapes` means "no shapes", not an error.
That is a **test**, not an intention; it is what keeps this a v2 extension rather than a
v3 migration.

**There is no v1 reader and there will not be one.** v2 is the only accepted version by
design (`session_reproducibility.md` §Known gaps).

## 2. `shapes` (new)

Source: `_shape_history` — the messages are **already replay-safe**; they were simply
never written into the document.

```jsonc
"shapes": [
  {
    "tag": "site1",
    "op": "add_sphere",              // the wire op — the shape's true type
    "options": { ... },              // the creation payload, verbatim
    "layer_tag": "binding site",
    "hidden": false
  }
]
```

- **`options` is stored verbatim**, not re-derived from the API. A shape *is* literal
  geometry (spec §4); re-deriving it would mean mapping the payload back onto keyword
  arguments — two vocabularies that will drift.
- **`hidden` is new** and is applied *after* the object is registered (no constructor
  takes it).
- `layer_tag` already rides inside `options` today; it is lifted to the record for
  symmetry with the other domains, and `options` remains the source of truth for the
  replay.

## 3. `layers` (new)

Without this key **an empty user layer cannot be restored** — it has no members to be
inferred from. That is the entire point of Contract S4b, and it is the key a naive
implementation will not think to add.

```jsonc
"layers": [
  { "tag": "binding site", "provenance": "user", "hidden": false }
]
```

- **Only `provenance == "user"` layers are serialised.** The degenerate auto-layers are
  rebuilt for free from their members' `layer_tag`; writing them out would fossilise
  noise.
- **`provenance` must be restored, not inferred.** Rebuild a user layer as `auto` and
  the cleanup deletes it the first time it is emptied — the bug this contract exists to
  remove, reappearing one round-trip later.

## 3.5 The annotation **anchor** becomes a structured object (new)

Today an annotation's anchor is a **flat list**, `options.atom_indices: [10]`. That
closes the door: the post-1.0 MVS work brings anchors that are free coordinates, or a
residue, or a chain (`post_1.0/annotations_mvs_machinery.md`), and none of them fit in a
list of atom indices. Adding them later would be a **format migration**.

Structure it now, while the format is open:

```jsonc
"anchor": { "type": "atoms", "indices": [10, 11, 12] }

// what it makes possible later, additively:
"anchor": { "type": "position", "xyz": [1.2, 0.4, 3.9], "unit": "nm" }
"anchor": { "type": "residue",  "residue_index": 42 }
```

- **Read both**: a document with the old flat `atom_indices` loads as
  `{"type": "atoms", "indices": [...]}`. **Write only the new form.** That is what keeps
  this a v2 extension and not a v3.
- `type` is the discriminator the **broken-anchor** state (Contract S7) reasons over: an
  anchor can be valid, damaged or destroyed, and *of a kind*.

**This is the cheapest possible moment to do it** — Phase 1 is already rewriting the
document. Doing it in Phase 6, or post-1.0, means migrating every saved session.

## 4. `annotations` and `measurements` — `hidden` (new)

Today both are stored as their **raw creation message** and nothing else:

```jsonc
{"op": "add_label", "tag": "mylabel",
 "options": {"text": "site", "tag": "mylabel", "layer_tag": "mylabel", "atom_indices": [10]}}
```

Add `hidden` to the record. Everything else the rebuild needs is already in `options`
(`picks_atom_indices`, `endpoint_policy`, `style`, `atom_indices`, `text`).

**The stored `value` and `value_series` of a measurement are *not* restored** — they are
**re-derived** when the recipe is executed (implementation plan §3). They stay in the
document as a record of what was measured, but the authority is the recipe, not the
number. Restoring a stale number onto coordinates that no longer match it is how a
figure comes out quietly wrong.

## 5. `tag_high_water_marks` (new)

```jsonc
"tag_high_water_marks": { "shape": 7, "annotation": 3, "measurement": 12, "layer": 2, "section": 0 }
```

Today only regions have these (`order_high_water_mark`, `uid_high_water_mark`) —
**because the rework already learned this lesson once, for regions, and did not
generalise it** (§0.9). Everyone else's counter resets to zero on reload, so the next
auto-generated `measurement1` collides with the imported one.

The `TagsManager` of Phase 0 owns this. On import, a counter is raised to
`max(current, stored)` — **never lowered**, or a viewer that already has objects would
start reissuing their tags.

The existing `order_` / `uid_high_water_mark` keys **stay where they are**: they are
region-specific (ordering and identity, not tag naming) and renaming them would be a
gratuitous format break.

## 6. What is *not* in the document, and why

| | why |
|---|---|
| **the structure** | The document is the **overlay** on a loaded structure. `import_state` requires a compatible structure already loaded. Whether a session should bundle its structure is an open product question (`session_reproducibility.md`). |
| **the scene history** | Session-scoped by design and deliberately not serialised (Contract H). A snapshot restores *where you are*; a history replays *how you got there*. Different mechanisms; do not conflate them. |
| **`render_status`** | Runtime diagnostics, not scene state. |
| **owned primitives** (Contract V) | Rebuilt from their owner's recipe, never serialised on their own. |
| **⚠ `sections`** | **They should be here and they are not** (§0.11). A clipping plane does not survive a save/reload. **Declared debt** — out of scope for this block, inherited by Viewport. Writing it down is the difference between a known gap and a silent break. |

## 7. Acceptance

- Every key round-trips **by content**, verified by mutation (drop the field → the test
  fails).
- A pre-Phase-1 v2 document imports cleanly.
- After an import, the model is **usable** — not just present (spec §6).
- `session_reproducibility.md` is updated: its "Known gaps" list currently does not
  mention that shapes, `hidden` and the counters were never serialised. It should now
  say so, and say that sections still are not.
