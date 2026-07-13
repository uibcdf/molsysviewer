# Phase 1 — The restore path (implementation plan)

**Status:** proposed (2026-07-12). Companion to
[the spec](phase1_state_restore.md) and
[the document format](phase1_state_restore_format.md).

**This document owns the *how*.** The spec says the model must be rebuilt; this says in
what order, with which calls, and which four traps will bite.

Prerequisite: **Phase 0** (the `TagsManager`s exist, so the high-water marks have a
home).

---

## 1. The rebuild order — and why it is not free

Objects have dependencies. Rebuild them in the wrong order and the result is not an
error; it is a **subtly wrong scene**.

```
1. tag high-water marks      ← before anything is created, or auto-tags collide
2. user layers               ← BEFORE their members (trap §2.1)
3. the whole                 ← representation, colour scheme, base colour layer
4. regions                   ← already topological (recipe operands before dependents)
5. annotations, measurements ← execute their recipes through the managers
6. shapes                    ← replay the message + register_shape_layer()
7. saved selections
8. active selection
9. clear the scene history   ← the old snapshots point at a different scene
```

### 1.1 The layer trap — the one that will be missed

A user layer must be created **before** the objects that belong to it.

Rebuild a shape with `layer_tag="binding site"` first, and `register_shape_layer()`
calls `_ensure_layer_group(...)`, which **creates the layer as `auto`**. It is then a
degenerate auto-layer as far as the model is concerned — so the moment the user empties
it, the cleanup **deletes it** (Contract S4b).

The user's carefully named layer evaporates one interaction after a reload, and nothing
raises. **Layers first, with their `provenance` from the document.**

## 2. The history must be suspended — and this is subtler than it looks

`records_scene_history._begin_operation()` calls **`export_state()`** on every mutating
operation (`scene_history.py:57-68`).

After this phase, `import_state` calls the managers. After Phase 3, those managers are
decorated. So a user-invoked `view.import_state(doc)` would:

- run a **full `export_state()` per rebuilt object** — O(N) full serialisations;
- and, far worse, **snapshot a half-built scene** into the undo stack. Those snapshots
  are *corrupt states* that the user can then "undo" into.

The mechanism already exists and is already used — but **only on the undo path**
(`scene_history.py:127-134`):

```python
def _restore(self, snapshot: dict) -> None:
    # Suspend checkpointing so import_state's own mutations do not push
    # new history entries.
    self._suspended = True
    try:
        self._view.import_state(snapshot)
    finally:
        self._suspended = False
```

**`import_state` must suspend the history itself**, not rely on its caller doing it. A
user calling `view.import_state(doc)` directly gets no protection today, and after this
phase that becomes a real defect.

And **afterwards it must `history.clear()`**: the pre-existing snapshots describe a
*different scene* (`clear()` is already what `load()` and `apply_system_edit` do —
`scene_history.py:120`). Undoing across an import is not a feature; it is a way to
restore a scene that no longer relates to the loaded structure.

> Note for Phase 3: `_depth` (the nesting counter) is **already** the transaction
> mechanism the coalescing needs. It does not have to be invented — only exposed.

## 3. The calls, per domain

**Recipe-bearing — execute through the public API** (Contract S2 applied to
deserialisation: the restore path may not reach past the public API either):

```python
measurements.add_distance(
    selection_a=record["options"]["picks_atom_indices"][0],
    selection_b=record["options"]["picks_atom_indices"][1],
    tag=record["tag"],
    layer_tag=record["options"].get("layer_tag"),
    endpoint_policy=record["options"].get("endpoint_policy"),
    measurement_style=record["options"].get("style"),
)
annotations.add_annotation(
    text=record["options"]["text"],
    atom_indices=record["options"]["atom_indices"],
    tag=record["tag"],
    layer_tag=record["options"].get("layer_tag"),
    label_style=record["options"].get("style"),
)
```

**The value and the series are re-derived**, and that is correct: a measurement is a
recipe over atoms and a policy, and the structure it is restored onto may not be
byte-identical. Do **not** restore the stored value — restoring a number that no longer
matches the coordinates is how a figure comes out quietly wrong.

**Geometry — replay the message and register the object:**

```python
shape = register_shape_layer(view, tag, layer_tag=..., meta=...)   # shapes/_registry.py
view._shape_history.append(msg)
view._send(msg)
if record.get("hidden"):
    shape.hide(skip_digestion=True)
```

`register_shape_layer()` is **the same function the creation path uses**. Rebuilding a
shape by calling `shapes.add_sphere(**options)` instead would map the *wire payload*
onto *API kwargs* — two vocabularies that will drift — and it would break on the first
one that diverges.

**Then apply `hidden`** for every domain. It is the field the naive implementation
forgets, because the object *looks* restored without it.

## 3.5 `_message_history` grows on every import — and undo imports

Measured 2026-07-12: importing the same document twice grows `_message_history`
from 2 → 7 → 12 entries. Each import appends its whole trace — `clear_scene`,
`clear_selections`, the re-creation ops, `clear_active_selection`, `set_atom_colors`.

**It is a leak, not a corruption.** The replay is self-correcting: each import emits its
`clear_scene` before re-creating, so replaying the accumulated history still lands on
the right scene. The final state is correct; the history is just unboundedly larger.

**But `_message_history` is what feeds the HTML export, the popup and the rebuild.** And
**undo is an `import_state`** (`scene_history.py:127`). So today, every undo already
adds ~5 junk messages — and **Phase 3, which puts every scene object under undo, will
multiply that by every operation the user performs.** A long session would export an
HTML file carrying hundreds of clear/re-create cycles: correct, and absurd.

**Therefore `import_state` must not append its rebuild to `_message_history` as if it
were user activity.** Either it rewrites the history to the post-import state (the
honest thing: after an import, the replay *is* the imported scene), or it suspends the
recording the way it suspends the scene history (§2) and re-seeds the history from the
restored document.

This is **pre-existing debt** — it is happening today — but this phase is where it
becomes visible and Phase 3 is where it becomes expensive. Fix it here.

## 3.6 Restoring onto a structure where the anchors are gone (Contract S7)

`import_state` may be given a document whose atom indices do not all exist in the loaded
structure. Rebuilding through the managers will then **raise**, halfway, leaving a
half-restored scene.

It must not. The object is rebuilt in the **`broken`** state (Contract S7) with its
reason, exactly as it would be after an `apply_system_edit` that removed its atoms. A
session must load — degraded and honest — rather than fail.

**This couples Phase 1 to Phase 4.** If Phase 4 has not landed, Phase 1 must still not
raise: it warns, marks, and continues. Decide it here, in the brief, rather than
discovering it when a user loads a session onto a stripped structure.

## 3.7 Two smaller things that will be forgotten

- **`skip_digestion=True`** on every rebuild call. The values came from a document this
  code wrote; re-validating each one through ArgDigest on import is pure cost.
- **`clear_first=False` — the collision policy, decided.** It is a supported argument of
  `import_state` (merge an overlay into a live scene). With the rebuild going through the
  managers with **explicit tags**, an imported object may collide with one already
  present.

  **Default: raise.** If an incoming `(kind, tag)` already exists, `import_state` refuses,
  naming the collision. Merging silently — overwriting, or quietly renaming — would
  produce exactly the kind of scene where the user cannot tell which `site1` they are
  looking at, which is the failure this block exists to remove.

  Offer the alternatives explicitly, never by default:

  ```python
  view.import_state(doc, clear_first=False, on_conflict="raise")   # default
  view.import_state(doc, clear_first=False, on_conflict="skip")    # keep mine
  view.import_state(doc, clear_first=False, on_conflict="rename")  # tag → tag_2
  ```

  Note the collision is on `(kind, tag)`, **not on `tag`** (Contract T): an imported
  *region* `site1` and an existing *shape* `site1` are not a conflict.

  Today this "works" only because nothing is ever registered — the bug of §0.8 hiding a
  second one.
- **Cost**: executing a measurement's recipe **re-derives its whole series**. Restoring
  20 measurements over a 100 000-frame trajectory recomputes 20 full series *at import
  time*. That is correct (spec §4) but it is not free. **Measure it**; if it bites,
  the cure is lazy series derivation, not restoring the stale stored value.

## 4. The traps, listed

1. **Layers before members** (§1.1) — or a user layer is reborn `auto` and evaporates.
2. **Suspend the scene history, then clear it** (§2) — or the undo stack fills with
   corrupt, half-built snapshots.
3. **Do not append the rebuild to `_message_history`** (§3.5) — or every import (and
   every undo) leaks ~5 messages into the replay that feeds the HTML export.
4. **High-water marks before creation** (§0.9) — or `import_state` restores
   `measurement1` and the next auto-tag is also `measurement1`.
5. **`hidden` is applied after creation, not passed to it.** No constructor takes it.
   Miss this and everything comes back visible, which looks like success.
6. **Missing anchors must produce a `broken` object, not an exception** (§3.6) — a
   session must load degraded rather than fail.
7. **One rebuild behaviour, not three.** Regions rebuild eagerly, selections lazily
   (`selections.py:186`), scene objects not at all. Land on **eager**: a lazily
   materialised object still reports an empty `tags()` and an empty registry, so the
   Phase 2 summaries would render nothing.

## 5. Files

| file | change |
|---|---|
| `molsysviewer/viewer/state.py` | the rebuild (the whole phase lives here) |
| `molsysviewer/scene_history.py` | `import_state` suspends + clears; expose the suspension |
| `molsysviewer/shapes/_registry.py` | (reused as-is — `register_shape_layer`) |
| `molsysviewer/viewer/scene_registry.py` | layer `provenance` honoured on rebuild |
| `tests/test_state_v2.py` | extended (§6) |

**No frontend changes.** If the diff touches `js/`, the phase has gone out of bounds —
the fix is entirely in the Python model. That is a useful property: this phase is
verifiable with `pytest` alone.

## 6. Tests — every one by mutation

**The test that defines the phase** (it fails today):

```python
v2.import_state(saved)
v2.measurements.hide('d1')                                    # today: ValueError
assert v2.measurements.info('d1')['visible'] is False
assert v2.measurements.count() == len(v2.measurements.tags()) # today: 1 != 0
```

**The shape round-trip** (today there is no `shapes` key at all):

```python
v2.import_state(saved)
assert v2.shapes.info('site1')[0]['color'] == '#FF8800'   # assert the CONTENT
assert v2.shapes.info('site1')[0]['radius'] == ...
```

**The hidden annotation** — mutate by dropping `hidden` from the record; the test must
fail.

**The empty user layer** — create a user layer, empty it, round-trip; it is still there,
still `user`. Mutate by dropping `provenance`; it comes back `auto` and evaporates.

**The counter** (§0.9):

```python
v2.import_state(state_with_measurement1)
v2.measurements.add_distance(...)        # auto tag
assert v2.measurements.count() == 2      # today: 1 — the new tag overwrote the old
```

**The old document** — a v2 document with no `shapes` key imports cleanly as "no
shapes". (This is the test that keeps the keys additive and the version at 2.)

**The history is not polluted** — after `import_state`, `len(view.history._undo) == 0`
and no snapshot describes a half-built scene.

**The replay history does not leak** (§3.5) — importing the same document twice does
**not** grow `_message_history`:

```python
v.import_state(doc); n1 = len(v._message_history)
v.import_state(doc); n2 = len(v._message_history)
assert n1 == n2          # today: 7 then 12
```

**A missing anchor degrades, it does not raise** (§3.6) — import a document onto a
structure whose atoms were stripped: the object comes back **`broken`**, and the rest of
the session still loads.

**`get()` stops lying** — after an import, `measurements.get('d1')` returns the object,
not `None`. *(That silent `None` is what would let calling code sail past a zombie.)*
