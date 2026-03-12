# Smoke Test

This page defines the short smoke test we should run now that MolSysViewer has:

- canvas interaction,
- context menus,
- measurement tool modes,
- `active_selection`,
- `GroupStrip`,
- persistent labels as `annotations`,
- and the first exploration -> reproducible-state bridges.

The purpose is not exhaustive regression coverage.
The purpose is to check:

- basic correctness,
- interaction feel,
- whether the UX matches the current contract,
- and whether reproducibility survives the exploratory path.

## Why Now

The project now has enough interaction surface that waiting longer increases the
cost of correcting UX and contract mismatches.

The smoke test should happen before adding much more interaction breadth.

## Principle

The smoke test should check both sides of the project leitmotiv:

- exploration must feel usable,
- and the relevant outcome of exploration must become reproducible viewer state.

## Scope

Current smoke scope:

1. Canvas selection and navigation
2. Context menu behavior
3. Interactive measurements
4. Active selection -> region
5. Active selection -> label
6. Interactive measurement -> persisted measurement
7. GroupStrip synchronization
8. Annotation API sanity after UI-created labels
9. Export/replay sanity for the newly created artifacts

## Recommended Test System

Use:

- `demo["dialanine"]`

Reason:

- small enough for fast iteration,
- enough groups to test labels and strip behavior,
- already used across regressions.

## Manual Smoke Flow

### 1. Open a real viewer

Create a viewer with a real molecular system and show it in a notebook/browser.

Suggested setup:

```python
from molsysviewer import demo

view = demo["dialanine"]
view
```

### 2. Check base mouse behavior

Expected:

- `left drag` rotates
- `right drag` pans/translates
- `right click` over the canvas opens the viewer menu, not the host menu
- `left click` on empty space clears `active_selection`

Record if any of these feel inconsistent or fragile.

### 3. Check element selection

Expected:

- `left click` on a visible element selects its `group`
- `Shift + left click` adds another selection item
- `double left click` focuses the target

Check in Python:

```python
view.get_last_active_selection_event()
```

Expected:

- element-oriented payload,
- `group_indices`,
- derived `atom_indices`,
- sensible metadata.

### 4. Check GroupStrip synchronization

Expected:

- click in canvas updates the strip
- click in the strip updates the canvas selection
- hover in the strip mirrors into viewer highlight
- `right click` in the strip opens the same context-menu family
- `double click` in the strip focuses the group

### 5. Check label creation from selection

Workflow:

- select exactly one group
- open the context menu
- choose `Add Label from Selection`
- enter text in the inline composer
- create the label

Expected:

- label appears in the scene
- compact label overlay appears in `GroupStrip`
- Python API sees it:

```python
view.annotations.info()
view.annotations.records()
```

### 6. Check region creation from selection

Workflow:

- select one or more groups
- open the context menu
- choose `Create Region from Selection`

Expected:

- a region is created
- it is usable from Python
- it survives the normal viewer state model

Suggested quick check:

```python
view.regions
```

### 7. Check interactive measurement

Workflow:

- right click on a target
- choose `Distance`, `Angle`, or `Dihedral`
- complete the required picks

Expected:

- visible in-canvas tool status
- `Esc` cancels the mode
- the measurement appears in the scene
- Python receives the last measurement-created event

Suggested check:

```python
view.get_last_measurement_created_event()
```

### 8. Persist the last measurement

Workflow:

- after a successful interactive measurement,
- open the context menu,
- choose `Persist Last Measurement`

Expected:

- a replayable measurement artifact is recorded
- it survives export/replay/rebuild semantics

Suggested checks:

```python
view.measurements.info()
```

If `info()` does not exist yet on measurements, at minimum inspect the exported
message history relevant to measurement ops.

### 9. Exercise annotation API robustness

After creating a label from the UI, check:

```python
view.annotations.tags()
view.annotations.count()
view.annotations.info()
view.annotations.set_text("...", "Edited")
view.annotations.set_group_index("...", 1)
view.annotations.hide("...")
view.annotations.show("...")
```

Expected:

- every operation updates the live viewer state coherently,
- no drift between frontend and Python registries,
- no replay/export corruption.

### 10. Check export/replay sanity

Suggested checks:

```python
msgs = view._build_export_messages()
```

Expected:

- created labels are present as annotation ops,
- persisted measurements are present as measurement ops,
- regions remain represented through the normal replay contract,
- no obvious contradictory stale operations remain after edits.

## Automated Portion

The automated smoke subset should remain small and fast.

Current minimum:

- `pytest tests/test_annotations.py -q`
- `pytest tests/test_reproducible_interaction.py -q`
- `pytest tests/test_measurements.py -q`
- `npm --prefix molsysviewer/js run test:js`
- `npm --prefix molsysviewer/js run test:e2e`

Notes:

- `test:e2e` is environment-dependent and may skip if browser/WebGL support is not available.
- A skip is an environment fact, not automatically a product failure.

## What To Record

When a smoke test reveals friction, record:

- exact gesture or workflow,
- expected behavior,
- observed behavior,
- whether the problem is:
  - correctness,
  - UX/feel,
  - reproducibility contract,
  - or environmental/setup.

Add the distilled result to:

- `devguide/checkpoints.md`

If the issue changes a stable decision, update the relevant design page too.

## Exit Criteria

The current smoke pass is good enough when:

- the main exploratory flows feel coherent,
- the viewer-owned context menu works in the real host environment,
- `GroupStrip` and canvas do not drift,
- labels and measurements can be turned into reproducible artifacts,
- and no major mismatch appears between the live UX and the current `devguide` contract.
