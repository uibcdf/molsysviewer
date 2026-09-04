---
summary: view.extract migrates overlay history messages but never registers the objects, so the extracted view cannot be saved.
issue: uibcdf/molsysviewer#74
status: open
opened: 2026-09-04
closed:
severity: high
verification: reproduced
area: [scene, state, tools]
guard:
normative:
blocked_by: []
supersedes: []
---

# `view.extract` gives back a view that cannot save itself

**Found:** 2026-09-04, while discussing whether the view needs a copy/extract mechanism of
its own (`uibcdf/molsysviewer#71`). It has one — `view.extract` — and its docstring
promises exactly what the discussion asked for:

> Return a new view built from a structural subset of this view. Regions, shapes,
> annotations, measurements, saved selections, and sections are migrated to the new view
> with atom indices remapped to the extracted subset.

Two of those five do not arrive.

## What happens

| | source | extracted |
| --- | --- | --- |
| `annotations.records()` | `['a1']` | **`['a1', 'a1']`** |
| `annotations.tags()` | `['a1']` | **`[]`** |
| `measurements.records()` | `['d1']` | `['d1']` |
| `measurements.tags()` | `['d1']` | **`[]`** |
| `regions.tags()` | `['prot']` | `['prot']` |

## Why it matters more than a wrong listing

`export_state()` on the extracted view raises `AttributeError: 'NoneType' object has no
attribute 'owner'` at `viewer/state.py:171`, because it resolves each measurement record
through `measurements.get(tag)` and receives `None`.

So an extracted view carrying a measurement **cannot be saved**, and because
`scene_history._scene_snapshot` calls `export_state`, **any scene-recording operation on it
crashes**. That is how this surfaced: adding a region to the extracted view raised, not
saving it.

The scene is drawn correctly — the messages were sent to the frontend. It is the Python
side that is missing its objects, which is the shape of defect this project treats as worse
than a visible failure: it looks right until you try to keep it.

## Cause

`tools/basic/extract.py` migrates history messages and only those:

```python
for msg in getattr(source, "_measurement_history", []):
    remapped = source._remap_measurement_message(msg, atom_index_map)
    if remapped is not None:
        result._measurement_history.append(remapped)
        result._send(remapped)
```

`records()` reads that history, so records appear. `tags()` and `get()` read an object
registry that nothing populates. Regions escape because they are migrated as objects.

The doubled annotation is consistent with the loop appending to `_annotation_history` and
then `_send`-ing a message whose normal handling appends again; not confirmed.

## The guard this needs

Extract a view carrying a measurement and an annotation, then `export_state()` it, and
assert `records()` and `tags()` agree on both sides. No test does that today, which is why
a capability this visible could be this broken.
