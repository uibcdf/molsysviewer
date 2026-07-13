# Studio subpanel — Measures (spec)

**Status:** proposed (2026-07-12). One of three documents for this subpanel:
this **spec** (what it is), the [UI design](studio_measures_subpanel_ui_design.md)
(what it looks like), and the
[implementation plan](studio_measures_subpanel_implementation_plan.md) (the seam,
field by field).

**Normative reference:** [`scene_objects_contracts.md`](scene_objects_contracts.md)
and, above it, [`scene_contracts.md`](../scene_contracts.md).

> **This document does not restate the contracts — it points at them.** The Whole
> subpanel spec of the rework went stale precisely because it *copied* normative
> semantics (`keep_hidden`) that later changed, and the collaborator would have
> implemented against a dead document. Rules live in the contracts. This spec says
> what the panel does and which API it calls.

---

## 1. What this panel is for

A measurement answers a quantitative question about the structure: *how far, what
angle, what torsion.* The panel is where the scientist **reads the numbers** and
manages the measurements that produce them.

Today it reads *"Distance — d1 · 2 picks"*. The number — **which is already in
the browser, in the creation message** — is thrown away by the controller
(`scene_objects_contracts.md` §0.6). The single most valuable thing this panel
can do is show it.

## 2. What the domain already offers

`view.measurements` (`molsysviewer/measurements.py`). No new Python API is needed
for this panel beyond what Phase 0 homogenises.

**Kinds and units** — the unit is a function of the kind, and is not negotiable:

| kind | endpoints | unit |
|---|---|---|
| `distance` | 2 | ångström |
| `angle` | 3 | degrees |
| `dihedral` | 4 | degrees |

**Creation.** `add_distance(sel_a, sel_b)`, `add_angle(sel_a, sel_b, sel_c)`,
`add_dihedral(sel_a, …, sel_d)`, each taking `tag`, `layer_tag`,
`endpoint_policy` and `measurement_style`.

**Reading.** `info(tag=None)` returns, per measurement: `kind`, `tag`,
`layer_tag`, `n_picks`, `picks_atom_indices`, `endpoint_kinds`,
`endpoint_policy`, `endpoint_labels`, `endpoint_atom_indices`, **`value`** (a
`puw` quantity, already in the right unit), `visible`, `active`.

**The series.** `series(tag)` returns the value across the **whole trajectory**
as a `puw` array. On a dynamic system this is the real content of a measurement —
not a number, a curve.

**Policy.** An endpoint that is a *group* of atoms must be reduced to a point.
`settings()` reports the policy; `set_endpoint_policy(policy)` sets it. Valid
values (`_MEASUREMENT_POLICIES`):

- `atom` — use the picked atom as-is.
- `centroid` — centroid of the picked atoms. **Default.**
- `representative_atom` — a named atom per molecule type, from
  `set_representative_atom(target, atom_name)`. Defaults: `protein: CA`,
  `nucleic: P`, `lipid: P`, `other: ""`.

**Lifecycle.** `show`, `hide`, `delete`, `clear`, `set_tag`, `set_layer_tag`,
`contains`, `get`, `count`, `records`, `tags()`.

## 3. The one trap: the value is frame-dependent

`info()` does not return "the value". It returns the value **at the active
frame** — internally `_active_series_index(len(value_series))` indexes into the
stored series.

So the Measures summary is **frame-dependent, exactly like a dynamic region**
(Contract R). Two consequences the implementation must honour:

1. The summary **must be re-synced when the trajectory frame changes**, or the
   panel will confidently display the value of a different frame. This is a
   *display correctness* bug, not a refresh nicety, and it is the kind of defect
   that no unit test catches unless it is written for it.
2. Re-syncing on every frame of a playing trajectory is a message per frame. The
   rework already paid for a ~3-second-per-message toll once
   (`scene_contracts.md` §0). The implementation plan must say what the update
   policy is, and it must be measured, not assumed.

## 4. Scope

**In:**

- Read the value, with its unit, per measurement.
- Read the series over the trajectory.
- Create a distance/angle/dihedral **from the active selection** — a
  GUI-native gesture that today has no button.
- The endpoint policy and the representative atoms (today reachable only from
  Python).
- Lifecycle: rename, layer, show/hide, delete, clear.

**Out:**

- **Re-rendering measurements with our own primitives.** A measurement is drawn by
  **Mol\*'s native measurement manager**
  (`plugin.managers.structure.measurement.addDistance`,
  `measurement-handlers.ts:281`), not by our shapes and annotations. Per
  Contract V that is its `renderer="native"`, and it stays: Mol\* gives us
  billboard label placement, dashes and picking for free, and reimplementing them
  with owned primitives is a large refactor with **guaranteed visual regression and
  no user-visible benefit**. It becomes worth revisiting once the Interactions
  domain has proven the owned-realisation model in anger.
- `measurement_style` (per-measurement visual styling): the API takes it and
  forwards it to Mol\* as `visualParams`, so the available knobs are **Mol\*'s
  vocabulary, not ours** — the control is parametric, not absolute. Exposing it is
  deferred deliberately, not forgotten.
- Deriving new quantities (RMSD, contact maps…): that is an addon's job, not the
  Measures panel's.
- Editing endpoints of an existing measurement: endpoints are atom-bound and the
  API offers no mutator (`Measurement.get_coordinates` is explicitly read-only).
  Delete and re-create.

## 5. What "done" means

- The panel shows the number, with units, and it is **correct at the current
  frame** while a trajectory plays.
- Every affordance goes through Python (Contract S2). Hiding a measurement from
  the panel makes `view.measurements.info(tag)['visible']` false — today it does
  not (§0.2).
- Deleting a measurement from the panel is **undoable** (Contract S6).
- A measurement's visibility and layer survive a save/reload (Contract S5).
