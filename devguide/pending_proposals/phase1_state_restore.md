# Phase 1 — The restore path must rebuild the model (spec)

**Status:** proposed (2026-07-12). One of three: this **spec**, the
[implementation plan](phase1_state_restore_implementation_plan.md) (how the rebuild
works) and the [document format](phase1_state_restore_format.md) (state v2, field by
field).

**Normative:** [`scene_objects_contracts.md`](scene_objects_contracts.md) §0.8, §0.9,
§0.11 and Contract **S5**; and the standing rule in
[`session_reproducibility.md`](../session_reproducibility.md), which this phase
enforces.

> Phase 0 and this one are the two dangerous phases, and they are the two that get
> three documents. Everything after them is comparatively safe **because** of them.

---

## 1. The defect, in one screen

`import_state` **restores the pixels but not the model.** It re-sends the raw creation
messages to the frontend (`state.py:148-156`) instead of going through the managers,
so `_ensure_layer()` — the only thing that ever constructs a `Measurement` or an
`Annotation` — is never called.

Save a session with a measurement `d1`, reload it, and:

| call | answers | reality |
|---|---|---|
| on the canvas | the measurement **is drawn** | ✅ |
| `.count()` | `1` | reads the history |
| `.tags()` | `[]` | reads `_scene_objects` — **empty** |
| `.info()` | `visible=False, active=False` | **a lie**: it is on screen |
| `measurements['d1']` | `KeyError` | loud |
| **`measurements.get('d1')`** | **`None`** | **silent — the worst of the three** |
| `.hide('d1')` | `ValueError: No measurement layer found` | cannot touch it |
| `.delete('d1')` | `ValueError` | cannot remove it |

The reloaded session shows objects the user **cannot manage** — from Python or from the
GUI — and the model contradicts **itself**: `count()` says one, `tags()` says none.

**And it fails in three different ways.** `__getitem__` raises, `hide()` raises a
*different* exception, and **`get()` quietly returns `None`** — so calling code sails
on believing the object does not exist. An inconsistent failure is worse than a clean
one, and the silent branch is the one that will hurt.

Verified by execution on 2026-07-12, not inferred.

### Selections are the exception — and that is its own problem

`view.selections` does **not** break, because `SelectionsManager.__getitem__`
**materialises the object lazily** (`selections.py:186`): the `_selections` registry is
empty after an import, yet `v.selections['pocket']` works.

So there are **three different rebuild behaviours** in the same codebase — eager
(regions, whole), lazy (selections), and absent (annotations, measurements, shapes).
Nobody chose that. This phase must land on **one**, and eager is the one the summaries
(Phase 2) require: a lazily-materialised object still gives an **empty `tags()`** and an
empty registry, so a panel built on the registry would render nothing.

## 2. And two more holes in the same wall

- **Shapes are not in the document at all** (§0.3). `export_state`'s keys are
  `version, annotations, measurements, selections, regions, whole, active_selection,
  order_high_water_mark, uid_high_water_mark`. **No `shapes`.** A `view.shapes.add_sphere(...)`
  does not survive a save/reload.
- **`hidden` does not round-trip** for annotations or measurements (§0.4): they are
  serialised as their raw creation message, so a hidden annotation comes back visible.
- **The tag counters do not survive** (§0.9), so after a reload the next auto-generated
  `measurement1` collides with the imported one.

## 3. Why this phase goes before the summaries and before undo

**Before the summaries (Phase 2)**: the authoritative summary is computed *from the
Python model*. Build it on top of a restore path that leaves the model empty and you
get a panel that **empties itself the moment the user reloads a session**, while the
canvas still shows the objects.

**Before undo (Phase 3)**: snapshot undo **is** an `export_state` / `import_state`
cycle. Applied to today's code it would (a) **silently delete every shape** — they are
not in the document — and (b) leave every measurement and annotation in the zombie
state of §1. Shipping undo first would not be useless: it would be **destructive**.

## 4. The rebuild rule: recipes are executed, geometry is replayed

Not every domain is rebuilt the same way, and getting this wrong is the main design
risk of the phase.

| domain | has a recipe? | how it is rebuilt |
|---|---|---|
| region | ✅ (provenance, mode) | **execute the recipe** — already topological, already correct |
| measurement | ✅ (picks + endpoint policy) | **execute it**: `measurements.add_distance(...)`. The value and the series are **re-derived**, which is right — the structure may differ. |
| annotation | ✅ (anchor atoms + text) | **execute it**: `annotations.add_annotation(...)` |
| **shape** | ❌ — it *is* literal geometry | **replay its message + register the object** (`register_shape_layer`) |

**A shape has no recipe to run.** Rebuilding it by calling `shapes.add_sphere(**options)`
would mean mapping the *wire payload* back onto *API keyword arguments* — two different
vocabularies — and it would break the moment they diverge. Its message is already
replay-safe; what is missing is only the **Python object**, and
`register_shape_layer()` is exactly the function that creates it at creation time.

That asymmetry is not a wart. It is Contract R showing through: **a region is a recipe,
a shape is a drawing.**

## 5. Scope

**In:**

- `import_state` rebuilds the **Python model**, through the managers for recipe-bearing
  objects and through the registry for shapes.
- `export_state` grows **`shapes`**, **`layers`** (with `provenance`), and `hidden` on
  annotations and measurements.
- The **tag high-water marks** for every domain (via the `TagsManager`s of Phase 0).
- **Backward compatibility**: a v2 document lacking the new keys loads cleanly. Additive
  keys — this stays **v2, not v3**.

**Out:**

- **Sections.** They do not serialise either (§0.11) and they *should*, but they belong
  to Viewport. **Declared debt**, not silently skipped.
- The panels. No GUI in this phase.
- Undo (Phase 3) — but this phase is what makes it safe.

## 6. What "done" means

The phase is **not** done when the parser stops raising. It is done when:

```python
v2.import_state(saved)
v2.measurements.hide('d1')      # ← works
v2.shapes['site1'].set_color('red')   # ← the shape is even there
assert v2.measurements.count() == len(v2.measurements.tags())   # ← the model agrees with itself
```

- A **shape round-trips with its colour and radius**.
- A **hidden annotation comes back hidden**.
- An **empty user layer survives** (its `provenance` is serialised).
- Auto-generated tags **do not collide** after a reload.
- An **old document** (no `shapes` key) imports cleanly as "no shapes".

Every one of these verified by **mutation**: remove the mechanism, the test must fail.
