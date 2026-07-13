# Studio subpanel — Measures (implementation plan)

**Status:** proposed (2026-07-12). Companion to
[the spec](studio_measures_subpanel.md) and
[the UI design](studio_measures_subpanel_ui_design.md).

**This document owns the seam.** Not the phase brief, not the spec. The single
most repeated defect of the scene rework was a field that crossed
Python → controller → panel and got **dropped at one of the intermediate
mappings**, with nothing failing — the panel just rendered a blank. So the seam
is specified here field by field, and the brief derives from it.

Prerequisites, all landed: **Phase 0** (Contracts T and S0 — identity, the
`TagsManager`s and the manager surface), **Phase 1** (Contract S5 — the restore
path rebuilds the model) and **Phase 2** (Contract S1 — the authoritative
summary). This panel is **Phase 5**.

**Contract T applies to every row.** A measurement is identified by
`("measurement", tag)`, not by `tag`: a region, a shape and an annotation may all
be called `site1` too. The `tag` in this panel's records and actions is therefore
*domain-local* — unambiguous only because the action names it
(`toggle_measurement_visibility`). Any op that reaches the runtime to address the
object must carry the `kind`, or it will hide the shape called `site1` instead.

---

## 1. The summary: one op per domain, not one for all

Contract S1 requires an authoritative summary pushed from Python. The op is
**per domain** — `set_measurement_summaries` — not a single lump for all scene
objects. Two reasons, both practical:

- A frame change invalidates **only** the measurement values (§3). A single
  combined op would re-push every shape and annotation on every frame, and this
  repo has already paid a ~3-second-per-message toll once
  (`scene_contracts.md` §0).
- It mirrors `set_region_summaries` / `set_whole_summary`, so there is one
  pattern in the codebase, not two.

### The summary must be re-sent on `ready` — or the panel is empty in the popup

A summary is sent with `_send_runtime_only`, so it **never enters
`_message_history`** and a frontend that attaches later never receives it by replay.
The `ready` handler re-sends them explicitly (`core.py:789-790`), and **the new
`_sync_measurement_summaries_runtime()` must be added there**.

Forget it and the panel renders **empty** — while the canvas shows the objects
happily — in the popup window, in a re-attached widget, after a kernel rebuild, and
in the standalone host. It will look perfect in the notebook it was written in and be
broken everywhere else.

## 2. The record, field by field

Python side, built **on `measurements.info()`** (Contract S1: one projection, not
two) in `viewer/regions.py`'s neighbouring style — a
`_measurement_summary_records()` + `_sync_measurement_summaries_runtime()` pair,
sent with **`_send_runtime_only`** (a summary is a projection of state, not a
command: it must never enter `_message_history` or it corrupts the replay).

| field | Python type | TS type | source | why the panel needs it |
|---|---|---|---|---|
| `tag` | `str` | `string` | `info()['tag']` | identity |
| `kind` | `str` | `"distance"\|"angle"\|"dihedral"` | `info()['kind']` | row label, and which unit |
| `value` | `float \| None` | `number \| null` | `info()['value']`, **magnitude only** | **the number** |
| `unit` | `str` | `string` | derived from `kind` | rendering `5.93 Å` / `112.4°` |
| `hidden` | `bool` | `boolean` | `not info()['visible']` | the eye, the dimming |
| `layer_tag` | `str \| None` | `string \| null` | `info()['layer_tag']` | `· layer: site` |
| `endpoint_labels` | `list[str]` | `string[]` | `info()['endpoint_labels']` | `N (res 1) → C (res 2)` |
| `endpoint_policy` | `str` | `string` | `info()['endpoint_policy']` | per-measurement policy shown on `⋯` |
| `n_picks` | `int` | `number` | `info()['n_picks']` | sanity, and the empty-value case |
| `atom_indices` | `list[int]` | `number[]` | flattened `endpoint_atom_indices` | focus |
| `series` | `list[float] \| None` | `number[] \| null` | `series(tag)`, magnitudes — **full, when it fits** (§3) | the value at the active frame, read locally |
| `sparkline` | `list[float] \| None` | `number[] \| null` | **min/max-bucketed** downsample of the series (§3) | the sparkline only — **never the displayed value** |
| `series_index` | `int \| None` | `number \| null` | active frame index | the marker on the sparkline |

Plus, once per push (domain-level, not per record):

| field | source | for |
|---|---|---|
| `endpoint_policy_default` | `settings()['endpoint_policy_default']` | the policy radio buttons |
| `representative_atoms` | `settings()['representative_atoms']` | the four inputs |
| `active_selection_count` | the active selection | *"Needs 2 picks · you have 1"* |

**`value` and `series` cross the wire as bare magnitudes, with `unit` beside
them.** A `puw` quantity is not JSON. Do **not** stringify the quantity in Python
and parse it in TS: that is a second unit system living in the frontend, and it
will drift. Python owns the unit; the panel formats.

## 3. Frame dependence — the trap, and how it is solved

`info()['value']` is the value **at the active frame** (`_active_series_index`).
Naively, that means re-syncing the summary on every frame — a message per frame at
30 fps, which would saturate the channel this repo has already had to rescue once
(`scene_contracts.md` §0).

**Solution: Python sends the series once; the frontend indexes it locally.**
Python pushes the whole series with the summary, and `viewer-controller.ts` updates
the displayed number and the sparkline marker **in JavaScript**, from the active
frame index. Python re-sends the summary only when a measurement is created,
deleted or edited — **and when the trajectory or the system changes**
(`load(mode="append_structures")`, `apply_system_edit`). That last clause is not
optional: without it the frontend keeps indexing a cached series that no longer
matches the frame count.

### The `series` / `sparkline` split — do not merge these two

They look like one field and they are two, and merging them **puts a wrong number
on screen**:

- **`series`** — the exact value per frame. This is what the frontend indexes to
  display `5.93 Å`.
- **`sparkline`** — a downsampled copy, **for drawing only**.

If the panel indexed a 200-point downsample with a frame index that runs to
100 000, it would render `undefined` — or, if someone "fixed" that by scaling the
index, **the value of a different frame, looking perfectly plausible**.

**The policy is a threshold**, and it must be measured, not assumed:

- series short enough (start at ~5 000 frames — most loaded trajectories):
  **send it whole**, the frontend indexes it, and the value is always exact;
- longer: send the `sparkline` for drawing, and refresh the exact `value`
  **throttled** (4–5 Hz, never 30) — a number flickering at 30 fps is unreadable
  anyway, so nothing is lost.

**Do not let the frontend recompute the value.** The endpoint policies (`centroid`,
`representative_atom`) mean the number is not a trivial distance between two atoms;
a second implementation would drift from Python's. Python owns the number
(Contract S1).

### Downsampling: min/max buckets, never a uniform stride

A uniform stride **deletes rare events**: at stride 500 a one-frame spike vanishes.
And a spike is precisely what the user is looking for in the sparkline of a
distance — the break, the jump, the brief excursion. A chart that hides the thing
you are looking for is worse than no chart.

Downsample with **min/max per bucket** (or LTTB). Same cost, and it does not lie.

This is the hardest thing in this panel. Implement it first, test it first.

## 4. The actions

New members of the closed `PanelAction` union (`js/src/ui/panels/types.ts:19`),
each with a handler in the `event == "interaction_context_action"` dispatcher in
`viewer/core.py` — that is the existing seam every panel action already uses
(`emitInteractionEvent({event: "interaction_context_action", action, ...details})`,
`viewer-controller.ts:1023`).

| action | payload | Python call |
|---|---|---|
| `create_measurement` | `{kind}` | `measurements.add_distance/add_angle/add_dihedral(...)` from the active selection |
| `toggle_measurement_visibility` | `{tag}` | `measurements.show(tag)` / `.hide(tag)` |
| `rename_measurement` | `{tag, new_tag}` | `measurements.set_tag(tag, new_tag)` |
| `set_measurement_layer` | `{tag, layer\|null}` | `measurements.set_layer_tag(...)` |
| `show_all_measurements` / `hide_all_measurements` | `—` | loop `show`/`hide` |
| `clear_measurements` | `—` | `measurements.clear()` |
| `set_measurement_endpoint_policy` | `{policy}` | `measurements.set_endpoint_policy(policy)` |
| `set_measurement_representative_atom` | `{target, atom_name}` | `measurements.set_representative_atom(...)` |

**Already exist, reuse — do not duplicate:** `delete_measurement` (`core.py:1437`)
already goes through Python correctly. Focus stays a local camera move.

**The one to remove:** the visibility toggle at `viewer-controller.ts:2934`,
which calls `handleMessage({op: "hide_layer"})` directly. It becomes
`toggle_measurement_visibility`. That deletion *is* the Contract S2 fix.

## 5. Files

| file | change |
|---|---|
| `molsysviewer/viewer/regions.py` (or a new `viewer/scene_summaries.py`) | `_measurement_summary_records()`, `_sync_measurement_summaries_runtime()` |
| `molsysviewer/viewer/core.py` | the new `interaction_context_action` handlers |
| `molsysviewer/js/src/ui/panels/measures-panel.ts` | **new** — replaces the generic `InspectorListPanel` for this tab |
| `molsysviewer/js/src/ui/panels/types.ts` | the new `PanelAction` members |
| `molsysviewer/js/src/ui/group-panel.ts` | mount `MeasuresPanel`; `setMeasurementSummaries()` |
| `molsysviewer/js/src/managers/viewer-controller.ts` | consume the summary; **delete** `addonsMeasurements` and its population sites |
| `molsysviewer/viewer.js` | **generated** — rebuild with `npm run build:runtime` as the **last** step. Never hand-edited. |

`InspectorListPanel` stays until Shapes and Annotations also have their own
panels; it is deleted in Phase 6, not here.

## 6. Tests

Every mechanism verified by **mutation**: revert it, its test must fail. A test
that still passes under mutation is hollow and does not count.

**Python**
- The summary record carries the **value with the right magnitude and unit** for
  each of the three kinds — asserted against `msm`-computed truth, not against
  `isinstance(float)`.
- **The frame-dependence test:** set frame *n*, read the summary, assert the
  value equals `series[n]`. Mutate by removing the re-sync on frame change → must
  fail. *This is the test that protects §3, and nothing else does.*
- Hiding from the panel action makes `info(tag)['visible']` false. (Today it
  stays true — that is the §0.2 mutation.)
- The endpoint policy round-trips and applies to **new** measurements only.

**JS unit**
- The row renders the value and the unit; a `null` value renders `—`, not
  `NaN` or `undefined`.
- Every affordance dispatches its `panel_action`. Assert **no** `handleMessage`
  is called for a state mutation — that assertion is the regression guard for the
  defect this phase removes.

**E2E, real browser** (`js/tests/e2e/`, the Phase 14 harness)
- Hiding a measurement from the panel removes it from the **Mol\* render tree**
  *and* Python reports it hidden. No unit test can prove both halves at once, and
  this is exactly the defect that shipped.
- Stepping a trajectory updates the displayed value.
