# Phase 0 — Identity and API coherence (implementation plan)

**Status:** proposed (2026-07-12). Companion to
[the spec](phase0_identity_and_managers.md) and
[the migration guide](phase0_identity_and_managers_migration.md).

**This document owns the seam — and here the seam is the whole codebase.** Contract T
changes what a *tag* means, and a tag is threaded through everything.

---

## 1. The size of it, measured

Counted 2026-07-12:

| | sites | where |
|---|---|---|
| **Python bare-tag indexing** | **84** | across **17 files** — `_scene_objects[…]`, `_layers.get(…)`, `_regions.pop(…)`, `_selections[…]` |
| **TS bare-tag indexing** | **28** | `tagIndex`, `layerMeta` (`state-handlers.ts`) |

**Over a hundred sites.** This is not a tidy-up; it is the largest phase of the block,
and the only one that cannot be deferred. Scope it honestly or it will be scoped for
you, halfway through.

## 2. The failure mode: silent aliasing

Every site left indexing by a bare tag will **merge two objects with no error and no
trace**. Not a crash — a wrong result that looks right. Hide the sphere `site1` and the
annotation `site1` disappears with it.

### The worst offender, and it is not obvious

`_rewrite_history_layer_tag` (`viewer/history.py:27-43`) rewrites **all three
histories** — `_shape_history`, `_annotation_history`, `_measurement_history` —
matching on the **bare tag**:

```python
self._shape_history       = self._rewrite_history_layer_tag(self._shape_history, old_tag, new_tag)
self._annotation_history  = self._rewrite_history_layer_tag(self._annotation_history, old_tag, new_tag)
self._measurement_history = self._rewrite_history_layer_tag(self._measurement_history, old_tag, new_tag)
```

Under Contract T, renaming the **shape** `site1` would silently rewrite the
**annotation** `site1`'s history entry too — corrupting the replay, the HTML export
and the popup. Nothing would raise. The figure would simply come out wrong, later,
somewhere else.

`_tag_from_message` (`history.py:16`) has the same shape and the same problem.

**Every history rewriter must become kind-aware.** This is the single highest-risk
edit in the phase.

## 3. The order of work (and why)

**1. Python model first, wire second, runtime last.** The kind must exist and be
correct in Python before anything downstream can trust it.

1. **`TagsManager`** per domain — the guards and the counters, with the high-water
   marks. No behaviour change yet beyond `regions` gaining a guard.
2. **Qualify the registries** — `_scene_objects` and `Layer.members` keyed by
   `(kind, tag)`. **Every one of the 84 sites is visited.** A site that still compiles
   after the key changes is a site that was silently ignoring the kind — treat a clean
   compile as suspicious, not as success.
3. **The history rewriters** (§2) — kind-aware. Highest risk; do it with its mutation
   test already written.
4. **The wire** — `hide_layer`, `show_layer`, `delete_layer`, `set_layer_tag` carry
   `kind`. Python sends it; TS reads it.
5. **`tagIndex` keyed by `(kind, tag)`** — the runtime already *receives* the kind
   (`registerTaggedRef(ref, tag, kind)`) and already stores it (`layerMeta`). It simply
   does not index by it. Use what is there.
6. **`LayersManager`**, `tags` → method, the six missing `shapes` methods (Contract
   S0).
7. **`docs/` migration** (see the [migration guide](phase0_identity_and_managers_migration.md)).

**Do not reorder 3 before 2.** Rewriting the histories against unqualified registries
is how you get a half-migration that passes its tests and corrupts exports.

## 4. The mandatory tests

These are not "nice coverage". Each one guards a defect that would otherwise ship
silently.

**The aliasing test — the one that defines the phase**

```python
# same tag, two domains
view.shapes.add_sphere(..., tag='site1')
view.regions.add(selection='...', tag='site1')

view.shapes.hide('site1')

assert view.shapes['site1']._hidden is True
assert view.regions['site1']._hidden is False     # ← the whole phase, in one line
```

**Mutation:** drop `kind` from the index key. **The test must fail.** If it still
passes, it is hollow and proves nothing.

**The history test** (§2)

```python
view.shapes.add_sphere(..., tag='site1')
view.annotations.add_annotation(text='...', tag='site1')
view.shapes.set_tag('site1', 'sphere1')

# the annotation's history entry must be untouched
assert any(r['tag'] == 'site1' for r in view._annotation_history)
```

**The counter test** (§0.9)

```python
v2.import_state(state_with_measurement1)
v2.measurements.add_distance(...)          # auto tag
assert v2.measurements.count() == 2        # today: 1 — the new tag collided
```

**The surface test** (Contract S0) — assert the canonical-surface table **by
introspection**, so the next manager cannot drift back out:

```python
for manager in (regions, selections, shapes, annotations, measurements, layers):
    for name in ("add", "tags", "count", "records", "info", "contains",
                 "get", "delete", "clear", "set_tag"):
        assert callable(getattr(manager, name))   # a method, never a property
```

**E2E, real browser.** Two objects sharing a tag; hide one; assert **only** its node
leaves the Mol\* render tree. The `tagIndex` bug is invisible to unit tests — it lives
in the runtime.

## 5. Files

| file | change |
|---|---|
| `molsysviewer/tags.py` | **new** — `TagsManager` |
| `molsysviewer/layers.py` | `LayersManager`; qualify `Layer.members` |
| `molsysviewer/viewer/scene_registry.py` | the guards delegate to the `TagsManager`s; qualify `_scene_objects` |
| `molsysviewer/viewer/history.py` | **kind-aware rewriters** (§2) — highest risk |
| `molsysviewer/viewer/core.py` | retire the five `_next_*_tag()`; `view.new_layer` deprecated |
| `molsysviewer/viewer/state.py` | high-water marks for every domain |
| `molsysviewer/shapes/__init__.py` | the six missing methods |
| `molsysviewer/{annotations,selections}.py` | `tags` property → method |
| `js/src/messages/viewer-messages.ts` | `kind` on the addressing ops |
| `js/src/managers/handlers/state-handlers.ts` | `tagIndex` keyed by `(kind, tag)` |
| `docs/` | the migration (breaking changes) |
| `devguide/architecture.md` | **rewrite §Key invariants 1** — it asserts a global tag uniqueness the code will not have |
| `molsysviewer/viewer.js` | **generated** — rebuild last. Never hand-edited. |

## 6. What this phase must not do

- **No GUI changes.** None. The phase must be verifiable on its own, and a panel change
  in the same commit would make the audit impossible to reason about.
- **No new domain behaviour.** Not colour, not visibility semantics, not serialisation
  beyond the high-water marks.
- **No `owner` field** (§0.12) — tempting, adjacent, and out.

If the diff touches `js/src/ui/panels/`, the phase has gone out of bounds.
