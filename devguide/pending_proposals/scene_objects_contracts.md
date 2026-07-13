# Scene-object contracts — shapes, annotations, measurements, layers

**Status:** proposed (2026-07-12). Candidate to be merged into
[`scene_contracts.md`](../scene_contracts.md) once implemented, exactly as
`region_contracts.md` was.

**Scope.** The four Studio subpanels that the scene rework did not touch:
**Measures**, **Annotations**, **Shapes** and **Layers** — and the Python
domains behind them (`view.measurements`, `view.annotations`, `view.shapes`,
`view.layers`).

The scene rework (15 phases, closed 2026-07-11) fixed the *structural* half of
the scene: the whole and the regions. It left the *non-structural* half — the
scene objects — on the pre-rework architecture. This document is the audit of
that half, and the contract it must satisfy.

> **The contracts in `scene_contracts.md` remain in force and win over this
> document.** Nothing here weakens Contract A, B, R or C.

---

## 0. Why this document exists (evidence)

Everything in this section was verified against the code and by executing it on
2026-07-12 — not inferred from the devguide. Each item names the defect and how
it was observed.

### 0.1 Three of the four panels are fed by a shadow state, not by Python

Whole and Regions, after the rework, are fed by an **authoritative summary
computed in Python** and pushed to the frontend (`set_region_summaries`,
`set_whole_summary` — `viewer/regions.py:523-621`). Python is the source of
truth; the panel renders what it is told.

Shapes, Annotations and Measurements are not. The frontend **rebuilds its own
copy of the state by watching the message stream go by**, into three maps
(`managers/viewer-controller.ts:562-564`):

```ts
private readonly addonsAnnotations  = new Map<string, { text; layerTag?; hidden; atomIndices }>();
private readonly addonsMeasurements = new Map<string, { kind; picks; layerTag?; hidden; atomIndices }>();
private readonly addonsShapes       = new Map<string, { title; subtitle?; layerTag?; hidden; atomIndices }>();
```

Python never sends a summary for these three domains. The panel can therefore
only ever show *what happened to appear in the creation message*, and only in
the shape the controller chose to keep. This is the root cause of every other
defect below, and the reason the three panels cannot be enriched without fixing
it first.

### 0.2 The panel's eye button reaches past the public API

**Precisely: the trash goes through Python, the eye does not.** `onDelete`
notifies `interaction_context_action` and Python handles it
(`core.py:1424-1440`, `delete_annotation` / `delete_shape` /
`delete_measurement`). `onActivate` (focus) is a camera move — local and
harmless. It is the **visibility toggle**, and only it, that mutates scene state
behind Python's back. The defect is surgical, not systemic — which is why it
survived unnoticed.

`viewer-controller.ts:2910`, `:2934` and `:2958` — the visibility toggle of
the Annotations, Measures and Shapes rows:

```ts
onToggleVisibility: () => {
    void this.handleMessage({ op: item.hidden ? "show_layer" : "hide_layer", tag });
},
```

`handleMessage` is the **local runtime dispatcher**: it repaints Mol\* and
returns. Python is never told. So `SceneObject._hidden` on the Python side goes
stale the moment the user clicks the eye, and every Python query that reports
visibility starts lying:

```python
view.annotations.info('mylabel')   # -> {'visible': True, ...}  after the GUI hid it
```

Compare with the Regions panel, which does it correctly:
`ctx.onAction("toggle_region_visibility", {tag})` → notify → Python →
`region.hide()` → Python state correct → `_send` → Mol\*
(`panels/regions-panel.ts:544`, `viewer/core.py`).

This is `engineering_rules.md` — *"the GUI never reaches past the public
API"* — violated in three panels. The Layers panel, notably, **already does it
right** (`set_layer_visibility` → `layer.hide()`, `viewer/core.py:1205`).

### 0.3 `export_state` does not serialise the shapes at all

Executed on a demo system (181L) with one sphere, one annotation and one
distance:

```
state v2 keys: ['active_selection', 'annotations', 'measurements',
                'order_high_water_mark', 'regions', 'selections',
                'uid_high_water_mark', 'version', 'whole']
shapes key present? -> False
```

**A `view.shapes.add_sphere(...)` does not survive a save/reload.** The user
saves their session, reopens it, and their shapes are gone — silently, because
`export_state` still returns a document and `import_state` still runs.

This is precisely the failure mode that
[`session_reproducibility.md`](../session_reproducibility.md) exists to
prevent ("serialisation coverage decays by default … and because `export_state`
still returns something, it breaks **silently**"). The promise was broken for
shapes and nobody noticed.

The fix is cheap: `_shape_history` already holds the replayable creation
messages (it is what the HTML export and the popup replay from). They are simply
never written into the session document.

### 0.4 `hidden` does not round-trip for annotations or measurements

Both are serialised as their **raw creation message**:

```
annotation record: [{'op': 'add_label', 'tag': 'mylabel',
                     'options': {'text': 'site', 'tag': 'mylabel',
                                 'layer_tag': 'mylabel', 'atom_indices': [10]}}]
```

There is no `hidden` in the record. The user hides an annotation, saves,
reloads — and it comes back visible. (Layer membership, by contrast, *does*
survive: `layer_tag` rides inside `options`.)

### 0.5 The scene history does not cover these four domains

`@records_scene_history` appears in `whole.py`, `regions.py` and
`active_selection.py`. It appears **nowhere** in `shapes/`, `annotations.py`,
`measurements.py` or `layers.py`.

So: recolouring a region is undoable; **deleting a measurement is not.** The
panels grow a delete (trash) button on rows whose deletion cannot be undone.
Contract H speaks of *one* scene-level history; these domains fell outside it.

### 0.6 The data is already crossing the seam — and being thrown away

The measurement creation message carries the computed value and its trajectory
series:

```
{'op': 'add_distance_measurement', 'tag': 'd1',
 'options': {..., 'value': 5.92789528892817, 'value_series': [5.9278...]}}
```

The controller parses that message into `{kind, picks, layerTag, hidden,
atomIndices}` — **dropping `value`** — so the panel row reads *"2 picks"*
instead of *"5.93 Å"*. The number the scientist actually wants is already in the
browser, and the GUI discards it. This is a pure GUI defect, not a plumbing one.

### 0.8 `import_state` restores the pixels but not the model

**The gravest defect found (2026-07-12), and the one that reorders the plan.**

`import_state` does not rebuild the Python objects. It **re-sends the raw creation
messages to the frontend** (`state.py:148-156`) instead of going through the
managers, so `_ensure_layer()` — the only thing that ever constructs a
`Measurement` or an `Annotation` (`measurements.py:229`, `annotations.py:212`) —
is never called. The histories are restored; `_scene_objects` is not.

Observed after saving a session with one measurement `d1` and reloading it:

| call | answers | reality |
|---|---|---|
| on the canvas | the measurement **is drawn** | ✅ |
| `.count()` | `1` | reads the history |
| `.tags()` | `[]` | reads `_scene_objects` — empty |
| `.info()` | `visible=False, active=False` | **a lie**: it is on screen |
| `.hide('d1')` | `ValueError: No measurement layer found` | cannot touch it |
| `.delete('d1')` | `ValueError` | cannot remove it |

So the reloaded session shows objects the user **cannot manage from Python or from
the GUI**, and the model contradicts *itself* — `count()` says one, `tags()` says
none.

Two consequences, both structural:

1. **Contract S1 cannot be satisfied without fixing this.** The authoritative
   summary is computed from the Python model. After a reload that model is empty,
   so the panel would render nothing while the canvas shows the measurements.
2. **Contract S6 (undo) would be actively destructive without fixing this.**
   Snapshot undo *is* an `import_state`. Adding `@records_scene_history` to the
   scene objects as the code stands today would leave every undone measurement
   and annotation in the zombie state above.

**The fix:** `import_state` must rebuild the model **through the managers**
(`measurements.add_distance(...)`, `annotations.add_annotation(...)`, …) — the
same public path a user takes — rather than replaying wire messages. That is
Contract S2 applied to deserialisation: *the restore path is not allowed to reach
past the public API either.*

### 0.9 The tag counters do not survive a reload

`_shape_counter`, `_annotation_counter`, `_measurement_counter`,
`_layer_counter`, `_section_counter` are **not serialised**. Only `regions` keeps
high-water marks (`order_high_water_mark`, `uid_high_water_mark`) — which exist
precisely because the rework already learned this lesson once, for regions, and
did not generalise it.

So after `import_state` the counter is back at zero and the next auto-generated
tag is `measurement1` — colliding with the `measurement1` that was just
imported. (`_next_annotation_tag` happens to loop until it finds a free tag;
`_next_shape_tag` and `_next_measurement_tag` do not.)

### 0.10 A structural edit silently deletes anchored objects — or silently staleness their value

**Executed 2026-07-12.** The real behaviour is not what a reading of `_remap_indices`
suggests, and it is worse. There are **two** failure modes, and they are opposite:

**(a) The object is silently deleted.** When an endpoint (or an anchor) loses *all* its
atoms, the whole object is discarded (`core.py:1928`):

```python
remapped_picks = [self._remap_indices(pick, atom_index_map) for pick in picks]
if any(len(pick) == 0 for pick in remapped_picks):
    return None          # ← the entire measurement is dropped
```

Delete atom 10, and the distance `0 → 10` **vanishes**. Same for an annotation whose
anchor atoms are gone. No error, no warning, no trace. The user edits their system and
**loses work they created**, and nothing tells them.

This is defensive — it avoids a corrupt object — but it is **mute**, and mute is not a
policy.

**(b) The object survives, showing a number computed from atoms that no longer exist.**
Far more insidious. A centroid endpoint over atoms `[0,1,2]` that loses only atom `2`
is *not* discarded — it is remapped to `[0,1]`. But **the stored `value` is not
re-derived**:

```
before edit:  2 endpoints, value = 0.43274799188494134
after  edit:  2 endpoints, value = 0.43274799188494134   ← identical, and now wrong
```

The centroid moved. The distance changed. The panel, the label and `info()` all report
the **old number** with complete confidence. **A wrong scientific value, presented as a
current one.**

This is the strongest argument in the whole block for two rules elsewhere: *never show a
stale number* (the panel designs), and *re-derive a measurement's value from its recipe
rather than restoring the stored one* (Phase 1, spec §4).

### 0.11 Sections do not serialise either — declared debt, not a clean non-goal

`export_state` has **no `sections` key** (verified: zero matches for `section` in
`viewer/state.py`), although `_section_history` exists and `Section` is a
`SceneObject` living in `_scene_objects`.

So a clipping plane the user positioned **does not survive a save/reload** — the same
silent break as the shapes (§0.3).

Sections are **out of scope** for this block (their panel is Viewport's, not one of
the four). But out of scope is not the same as fine: this is **declared debt**, and it
is written down here so that closing this block cannot be mistaken for closing
`session_reproducibility.md`'s promise. Whoever owns Viewport inherits it.

### 0.12 Add-on shapes are ordinary shapes — and the panel will let the user delete them

Add-ons do not have a private channel. They create shapes by **calling the public
API** — the live example is ElasNetMT:

```python
layer = view.shapes.add_displacement_vectors(...)   # adapters/modes.py:88
layer = view.shapes.add_links(...)                  # adapters/contacts.py:83
```

(`AddonShapeProviderSpec` is declarative metadata; it is not the creation path.)

So an add-on's shape lands in `_scene_objects` like any other, appears in
`shapes.info()`, and will therefore **appear in the Shapes panel with a trash button
next to it**.

**Decision: that is correct, and it stays.** It is the user's scene; a viewer that
shows an object it refuses to let you remove is worse. Two consequences that must be
honoured rather than discovered:

- **An add-on must tolerate its shape being deleted.** The handle it kept goes
  `_active = False`; it must check, not assume. This belongs in the add-on contract.
- **The panel should say where an object came from.** There is no `owner` field in the
  model today, so a shape from ElasNetMT is indistinguishable from one the user made.
  Adding `owner` to the record (and showing `· from elasnetmt` on the row) is cheap,
  genuinely useful, and **explicitly deferred** — it is API surface, and this block has
  enough. Recorded so it is a choice and not an oversight.

### 0.7 Three of the panels do not exist

There is no `measures-panel.ts`, no `annotations-panel.ts`, no
`shapes-panel.ts`. The three tabs share one generic `InspectorListPanel`
(`panels/inspector-list-panel.ts`, 75 lines) that renders a flat list of rows —
title, subtitle, focus, eye, trash — and differs only in its labels. Layers has
a real panel (281 lines), but assigns a region to a layer by **typing both tags
into two text boxes**.

---

## 1. What the API already offers that the GUI does not expose

This is the substance the subpanels are missing. None of it needs new Python
API — it needs to be surfaced. (Verified against the modules on 2026-07-12.)

**Measurements** (`measurements.py`)
- `info()` → `kind`, `n_picks`, `endpoint_labels`, `endpoint_policy`,
  `endpoint_kinds`, **`value` (a `puw` quantity)**, `visible`, `layer_tag`.
- `series(tag)` → the value across the **whole trajectory** — the natural
  content of a Measures panel over a dynamic system, and a plot the panel could
  own.
- `settings()`, `set_endpoint_policy()`, `set_representative_atom()` — the
  measurement policy, today configurable only from Python.
- `add_distance` / `add_angle` / `add_dihedral` — creating a measurement from
  the active selection is a GUI-native gesture with no button.
- `set_tag`, `set_layer_tag`, `show`, `hide`, `delete`, `clear`.

**Annotations** (`annotations.py`)
- `add_annotation(text, kind=…)` — note `add_label()` is **deprecated**; the
  panel must not grow on top of a deprecated entry point.
- `set_text(tag, text)` — edit an annotation **in place**; the panel has no
  rename/edit affordance at all.
- `set_anchor(...)`, `set_group_index(...)` — re-anchor a label to another atom
  group.
- `info()` → `kind`, `text`, `n_atoms`, `atom_indices`, `visible`, `layer_tag`.

**Shapes** (`shapes/`)
- **14 shape types** (sphere, links, hbonds, channel tube, tetrahedra, triangle
  faces, pocket blob, pocket surface, alpha spheres, scalar/gaussian
  isosurface, rings, anisotropy ellipsoids, displacement vectors,
  pharmacophore/interaction sites).
- `info()` → `kind`, `tag`, `layer_tag`, `color`, `radius`/`width`, `center(s)`,
  `visible` — already a panel-ready summary.
- `render_status()` → runtime diagnostics for trajectory-bound shapes (whether
  a dynamic shape resolved on this frame). A Shapes panel that shows *nothing*
  about render failures is hiding the one thing the user needs when a shape does
  not appear.
- On each `Shape` object: `set_color`, `set_colors`, `set_alpha`, `set_radius`,
  `set_radii`, `set_radius_scale`, `set_length_scale`, `set_center`,
  `get_coordinates`, `set_coordinates`, `focus`. **None of this is reachable
  from the GUI.**

**Layers** (`layers.py`)
- `Layer.info()` → per-member `kind`, `tag`, `visible`, `type`.
- `Layer.attach(obj)` / `Layer.detach(obj)` — the panel disables its "Remove"
  button for scene objects with the tooltip *"Scene objects are managed by
  their own addon layer tags"*, **which is false**: `detach()` exists and works.
- `Layer.set_tag()` — rename a layer. No GUI.
- `members` — regions **and** scene objects. The panel groups both, but can only
  act on regions.

---

## 2. The contracts

**Naming.** Two cross-cutting contracts carry a mnemonic letter — **T** (tags and
identity) and **V** (visual realisation) — because they govern *every* domain,
including the future ones. The **S** series is the scene-object series proper. The
existing contracts in [`scene_contracts.md`](../scene_contracts.md) (A, B, R, C, H)
remain in force and **win over everything here**.

They appear below in dependency order — **V is deliberately before S5**, because
serialisation cannot say what an *owned* primitive is until ownership is defined.

| | contract | in one line |
|---|---|---|
| **T** | Identity | An object is `(domain, tag)`, not `tag`. Each domain owns a `TagsManager`. |
| **S0** | Managers | Every scene domain has a manager, and they all look the same. |
| **S1** | Source of truth | Python computes the authoritative summary; the frontend keeps no shadow copy. |
| **S2** | GUI via the API | Every affordance calls the public Python method. No panel touches the runtime. |
| **S3** | Visibility | One channel: an object is hidden **iff** Python's `_hidden` says so. |
| **S4** | Layer membership | Two channels (`obj.layer_tag` vs `region.layer`), and it bites. |
| **S4b** | Layers are entities | A layer has `provenance`; a user layer survives empty. |
| **V** | Visual realisation | A domain object *owns* its realisation; it *is* not that realisation. |
| **S5** | Serialisation | Every scene object round-trips — recipe, visibility, layer (extends C). |
| **S6** | History | Every scene mutation is undoable, and continuous gestures coalesce (extends H). |
| **S7** | Broken anchors | A vanished anchor is a *state*, never a silent truncation. |

### Contract T — Identity is `(domain, tag)`, not `tag`

**Decision (2026-07-12): ADOPTED.** A scene object is identified by the pair
**(domain, tag)**. A tag is unique **within its domain**, not across the scene.

**The domains, and where each keeps its tags today:**

| domain | registry | guard today |
|---|---|---|
| `region` | `_regions` | **none** |
| `shape` / `annotation` / `measurement` / `section` | `_scene_objects` (**shared**) | `_assert_scene_object_tag_available` |
| `layer` | `_layers` | `_assert_nonstructural_tag_available` |
| `selection` | `_selections` | its own, inline (`selections.py:395`) |

**Four registries, three guards, and no shared rule.** `section` (the clipping
planes) is a domain by class though its panel lives in Viewport; `selection` (saved
selections) is a domain too — it has a tag, a registry and a uniqueness check, and it
must not be forgotten just because it draws nothing.

So `site1` may legitimately be, at once, the **region** that defines a binding
site, the **shape** that marks it, the **measurement** that quantifies it and the
**annotation** that labels it. That is how the science reads, and forcing
`site1_region` / `site1_sphere` is a friction the user would pay in every
session, forever.

#### Why this is a decision and not the status quo

Today the system is *half* one and *half* the other, with no principle behind the
line:

- `_regions` is its own namespace with **no guard at all** —
  `view.regions.add(tag='x')` succeeds while a shape `x` exists (verified
  2026-07-12).
- `_scene_objects` is **one shared namespace** for shapes, annotations and
  measurements — a shape and an annotation *cannot* share a tag
  (`_assert_scene_object_tag_available`).
- `_layers` is a third namespace with its own guard.

And `architecture.md` §Key invariants 1 asserts *"Tag uniqueness is global. A tag
can appear in `_scene_objects` OR in `_layers`, never both"* — which is **false in
the normal case**: creating a shape `x` registers `x` in `_scene_objects` **and**
in `_layers` (its degenerate auto-layer). **That invariant must be rewritten when
this lands.**

The six tag counters (`_region_counter`, `_shape_counter`,
`_annotation_counter`, `_measurement_counter`, `_layer_counter`,
`_section_counter`) already think per-domain. The code just never sustained it.

#### What it requires

**1. Each domain owns its tag policy: a `TagsManager` per domain.**

The uniqueness authority of a domain is an object, not a scattering of methods.
Today the tag logic is smeared across six counters on the view
(`_shape_counter`, `_region_counter`, …), two asymmetric guards in
`scene_registry.py`, and five `_next_*_tag()` helpers in `core.py` — and
`regions` has no guard at all.

`TagsManager` (one instance per domain) owns:

- the **prefix and the counter** (`shape1`, `measurement1`, …);
- **uniqueness within the domain** — the guard `regions` never had;
- **allocation** of the next free tag, and **validation** of a user-supplied one;
- the **high-water mark**, serialised with the session (§0.9: today the counters
  reset to zero on reload and the next auto-tag collides with an imported one —
  only `regions` was ever fixed, and the fix was never generalised).

**It must not keep its own list of live tags.** If it did, there would be two
sources of truth about what exists — the `TagsManager` and the domain registry —
and they *will* diverge; that is the exact sin Contract S1 forbids. It owns the
**naming policy** and **asks** the registry what exists.

That is the whole justification for the class: without the high-water mark and the
uniqueness guard it would be an anaemic wrapper around an integer, and it would
not earn its place.

**2. The wire must type its addressing.** This is the real work. Today the
addressing ops carry a **bare tag**:

```ts
export type HideLayerMessage   = { op: "hide_layer";   tag?: string };
export type DeleteLayerMessage = { op: "delete_layer"; tag?: string };
```

and `tagIndex` (`state-handlers.ts:120`) is a `Map<string, Set<Ref>>` keyed by the
bare tag. Under Contract T a bare tag is **ambiguous**, so:

- the addressing ops (`hide_layer`, `show_layer`, `delete_layer`,
  `set_layer_tag`, …) carry the `kind`;
- `tagIndex` is keyed by `(kind, tag)`.

**The kind already exists on both sides — use it, do not invent it.** Python:
`SceneObject.kind` (`layers.py`). Runtime: `layerMeta: Map<tag, {kind}>` and
`registerTaggedRef(ref, tag, kind)` (`state-handlers.ts:239`) — the runtime is
*already told* the kind of every ref and simply does not index by it.

**3. `_scene_objects` must be qualified.** It is one flat dict shared by shapes,
annotations, measurements and sections. Under Contract T two of them may share a
tag, so the registry key becomes `(kind, tag)` (or it splits per domain). Decide
in Phase 0 and apply it *everywhere the registry is walked* — this is where the
aliasing will hide.

**4. `Layer.members` must be qualified.** It returns a dict keyed by tag mixing
regions and scene objects. Under Contract T two members of different domains may
share a tag and one would silently overwrite the other in that dict.

#### What it fixes for free

The **degenerate auto-layer** stops being a tolerated collision that contradicts
the docs, and becomes **legal by construction**: the layer `x` and the object `x`
are different domains, so the same name is simply allowed (Contract S4).

#### The risk, stated plainly

**Silent aliasing during a partial migration.** Any site left indexing by a bare
tag will merge two objects with no error and no trace: hide the sphere `site1`
and the annotation `site1` vanishes too. This repo has shipped this class of
defect before.

Non-negotiable mitigation, verified by mutation: **create the same tag in two
domains, mutate one, assert the other does not move.** If that test passes with
the `kind` removed from the index key, the test is hollow.

### Contract S0 — Every scene domain has a manager, and they all look the same

**Decision (2026-07-12): ADOPTED — full homogenisation, breaking changes
accepted (pre-1.0).**

The five managers were grown independently and drifted. Measured on 2026-07-12
by introspecting the classes:

| | regions | selections | shapes | annotations | measurements |
|---|---|---|---|---|---|
| `add` | method | method | — (`add_sphere`…) | — (`add_annotation`) | — (`add_distance`…) |
| **`tags`** | **method** | **PROPERTY** | **method** | **PROPERTY** | **method** |
| `count` | method | method | **—** | method | method |
| `records` | method | method | **—** | method | method |
| `info` | method | method | method | method | method |
| `contains` / `get` / `clear` | method | method | method | method | method |
| `delete` | method | method | **—** | method | method |
| **`show` / `hide`** | — | — | **—** | method | method |
| `set_tag` | method | method | **—** | method | method |
| `set_layer_tag` | — | — | method | method | method |

Two things this table shows:

**`tags` is a property in two managers and a method in three.** So
`view.measurements.tags()` works and `view.annotations.tags()` raises
`TypeError: 'list' object is not callable`. A trap that is only ever found by
walking into it.

**`shapes` is the poorest manager of the five** — no `count`, `records`,
`delete`, `set_tag`, `show` or `hide`. To hide a shape you must drop to the
object (`view.shapes['tag'].hide()`), while annotations and measurements offer
`view.annotations.hide(tag)`.

That last row is not a cosmetic gap. **It is very likely the historical reason
the Shapes panel bypassed Python and called `handleMessage` directly** (§0.2):
the API did not offer it the same moves it offered the others. The architectural
defect and the API gap are the same wound.

**The canonical manager surface.** Every scene domain exposes:

- creation: **`add(...)`** where the domain has one kind; `add_<subtype>(...)`
  where it genuinely has subtypes (shapes, measurements). The verb is always
  `add` — never `new`. (`view.new_region` → `view.regions.add` was migrated in
  Phase 13 for this reason; do not reintroduce the inconsistency.)
- query: `tags()`, `count()`, `records()`, `info(tag=None)`, `contains(tag)`,
  `get(tag)`, and `__getitem__`.
- lifecycle: `delete(tag)`, `clear(tag=None)`, `set_tag(tag, new_tag)`.
- visibility: `show(tag)`, `hide(tag)`.
- grouping: `set_layer_tag(tag, new_layer_tag)` where the domain has layers.

**`tags` becomes a method everywhere.** This breaks `view.annotations.tags` and
`view.selections.tags`; `docs/` must be migrated in the same phase. Pre-1.0 is
when this is cheap; after 1.0 it is not.

`annotations.add_annotation()` stutters and `layers` has no verb at all; both
are covered above.

### Contract S1 — Python is the source of truth for every scene object

A scene object's state (existence, tag, kind, layer membership, visibility, and
every domain attribute the panel shows) lives in Python. The frontend **must
not** maintain a parallel model of it reconstructed from the message stream.

Python computes an authoritative summary and pushes it, following the molde
already established for regions (`viewer/regions.py:569`):

```python
def _measurement_summary_records(self) -> list[dict]:  ...
def _sync_measurement_summaries_runtime(self) -> None:
    self._send_runtime_only({"op": "set_measurement_summaries", ...})
```

**One op per domain** (`set_measurement_summaries`, `set_annotation_summaries`,
`set_shape_summaries`), not one lump for all scene objects: a trajectory frame
change invalidates only the *measurement* values, and a combined op would
re-push every shape and annotation on every frame. This repo has already paid a
~3-second-per-message toll once (`scene_contracts.md` §0).

#### A summary is runtime-only — **so it must be re-sent on `ready`**

This is the corollary that is easiest to miss and most expensive to miss.

Because a summary is sent with `_send_runtime_only`, it **never enters
`_message_history`** — which is exactly what we want (it is a projection of state,
not a command, and putting it in the history would corrupt the replay). But it means
**a frontend that attaches later never receives it by replay.**

That is why the `ready` handler re-sends them explicitly (`core.py:789-790`):

```python
elif event == "ready":
    self._ready = True
    self._pending_messages.clear()
    self._sync_region_summaries_runtime()
    self._sync_whole_summary_runtime()
```

**Every new `_sync_<domain>_summaries_runtime()` must be added there.** Forget it and
the panel renders **empty** — while the canvas happily shows the objects — whenever
the frontend attaches fresh: **the popup window, a re-attached widget, a rebuilt
kernel, a standalone host**. It will look fine in the notebook you developed it in
and be broken everywhere else.

There must be a test that opens a fresh frontend and asserts the panel is populated.

Two more rules that the region implementation earned the hard way:

- Use **`_send_runtime_only`**: a summary is a projection of state, not a
  command. It must not enter `_message_history` or it will corrupt the replay.
- **Every mutation of a scene object must re-sync the summary**, including
  mutations that arrive indirectly (a layer hide that hides its members; a
  rebuild after `apply_system_edit`). The counter-staleness trap in Phase 12 was
  exactly this: a summary that was correct on creation and wrong ever after.

The summary should be **built on the `info()` that each manager already
exposes** (`shapes.info()`, `annotations.info()`, `measurements.info()`), not on
a second, parallel projection. Two projections of the same state will drift.

### Contract S2 — The GUI acts only through the public Python API

Every mutating affordance in the Measures, Annotations, Shapes and Layers
panels dispatches a `panel_action` to Python, which calls the same public method
a user would call from a notebook. No panel may call `handleMessage` to mutate
Mol\* state directly.

The consequence is a guarantee, and it is the point of the contract: **anything
the user can do in the GUI, they can do from Python, and the Python state
afterwards is identical.**

Corollary: the visibility toggles at `viewer-controller.ts:2910/2934/2958` are
defects, not shortcuts. They must be routed through Python (`annotations.hide()`
etc.), as Regions and Layers already are.

### Contract S3 — Visibility has one channel

A scene object is hidden **iff** its Python `_hidden` is true. There is no
second source of visibility truth. The GUI reads it from the summary and writes
it through the API.

### Contract S4 — Layer membership: two channels, and it bites

Scene objects carry membership in **`obj.layer_tag`**; regions carry it in
**`region.layer`**. This asymmetry is already recorded in `architecture.md`
(§Key invariants 2) because a layer rename once silently orphaned every region
in the layer by writing the wrong field.

Any code that walks `Layer.members` **must branch on which channel the member
uses**. The Layers panel must show, and be able to act on, both kinds of member:
regions via `region.set_layer()` / `remove_from_layer()`, scene objects via
`obj.set_layer_tag()` / `Layer.detach(obj)`.

A layer with a single member whose tag equals the layer's tag is a *degenerate*
layer: the object's own auto-layer (`SceneObject.__init__` sets
`self.layer_tag = layer_tag or tag`), not a user-made group.

**The panel presents them as groups today.** `buildLayers()`
(`panels/layers-panel.ts:105-113`) groups by any non-empty `layerTag`, and a
loose object's `layerTag` *is* its own tag — so three unrelated spheres render as
three one-member "Layer Groups", and the tab badge counts them. A layer group is
a **user-made** grouping; the degenerate auto-layers must be filtered out of the
panel (they remain in the model, where they are load-bearing).

### Contract S4b — A layer is an entity, not a side effect of its members

**Decision (2026-07-12): ADOPTED.** `view.layers.add(tag)` becomes public API,
and an **empty layer is legal**: it can be created, renamed, populated later, and
it survives a save/reload.

**The verb is `add`, and it is not a free choice — it is the house style:**

| domain | accessor | creation |
|---|---|---|
| regions | `view.regions` → `RegionsManager(dict)` | `.add(...)` |
| selections | `view.selections` → `SelectionsManager` | `.add(...)`, `.add_from_active_selection(...)` |
| shapes | `view.shapes` → `ShapesManager` | `.add_sphere(...)`, … |
| annotations | `view.annotations` → `AnnotationsManager` | `.add_annotation(...)` |
| measurements | `view.measurements` → `MeasurementsManager` | `.add_distance(...)`, … |
| **layers** | `view.layers` → **`Mapping[str, Layer]`** | **`view.new_layer(...)`** — on the *view*, not the manager |

Layers is **the only domain with no manager at all** (`core.py:1706` returns the
raw `_layers` registry), which is precisely why its creation verb had to hang off
the view itself. `view.new_layer()` (`scene_registry.py:138`) is the **last
survivor of the pre-Phase-13 style**: it is the same shape as the
`view.new_region()` that was migrated to `view.regions.add()` in that phase.
Deprecate it, migrate `docs/`, remove it.

So this is not "add a method": it is *give layers the manager every other domain
already has.*

`LayersManager` must copy the `RegionsManager` mould — **a `dict` subclass** — so
that `view.layers['mylayer']`, iteration and `len()` keep working exactly as they
do today (the registry is used as a plain dict all over the codebase), while the
manager gains `.add()`, and the natural home for `.tags()`, `.contains()`,
`.info()`, `.delete()`.

`view.new_region` was migrated to `view.regions.add` in Phase 13 of the rework
for exactly this reason. Do not reintroduce the inconsistency here.

This settles an invariant that today **contradicts itself**. Verified 2026-07-12:

- A layer **created empty survives** — `view.new_layer(tag='empty1')` persists in
  `_layers` indefinitely. Empty is legal *at birth*.
- A layer that **becomes** empty is **deleted** — put one member in it, take it
  out, and it is gone (`scene_registry.py:80-81` and
  `_cleanup_empty_layer_group:90-91` both `pop` it).

So an empty layer is legal when created and illegal when emptied. That is worse
than either rule on its own: the user creates a layer, drags its only member out
to reorganise, and the layer silently evaporates.

Under this contract a **user layer survives empty, always.** The auto-cleanup
cannot simply be deleted, though — it is what stops the degenerate auto-layers
accumulating. The two must therefore be **told apart**, the way a region carries
its `provenance`:

#### The mechanism: `Layer.provenance = "auto" | "user"`

- a layer born **for** an object (its degenerate auto-layer) is **`auto`**;
- a layer the user creates (`layers.add`, or by naming a new layer when assigning a
  member) is **`user`**;
- **adding any further member to an `auto` layer promotes it to `user`** — it has
  stopped being one object's shadow and become a grouping;
- **on becoming empty, a layer is auto-deleted only if `provenance == "auto"`.** A
  `user` layer persists empty, ready to be filled again.

There is **no demotion**: a `user` layer that loses its members stays `user`.
Silently degrading it would make it evaporate later, which is the bug we are
removing.

Two things this mechanism must not forget:

- **`provenance` serialises** (Contract S5). Without it, every layer is reborn
  `auto` on reload and the user's empty layers evaporate on first use — the same
  bug, one round-trip later.
- **Promotion must cover regions too.** A region carries its membership in
  `region.layer`, **not** in `layer_tag` (Contract S4). Code that only watches
  `set_layer_tag` will never promote a layer that a region joined — and that
  asymmetry has already orphaned regions once in this repo.

So:

- a **user layer** — created explicitly (`layers.add`, or by naming a new layer
  when assigning a member), or promoted. Survives empty. Renameable. Serialised.
- a **degenerate auto-layer** — the object's own `layer_tag == tag`. Cleaned up
  when empty, never shown in the panel, never serialised as a group.

`Layer.delete()` deletes its **members** today. For a user layer the panel needs
*delete the group, keep the objects* (detach them) as well. Deciding which one
the trash button means — and offering both — is part of the Layers subpanel
design, not an implementation detail.

### Contract V — A domain object *owns* its visual realisation; it *is* not that realisation

**Decision (2026-07-12): ADOPTED**, after establishing that a measurement — and
tomorrow an interaction — is visually a *composition* (a line plus a label), and
asking whether it should therefore simply **be** a layer of shapes and
annotations.

**It should not.** The distinction is the one already accepted for regions: a
region is not a cartoon, a region **has** a representation — which is precisely why
it can change it. Collapse the object into its drawing and the questions have no
answer: where does the value `5.93 Å` live? The endpoint policy, the time series,
the Luzar–Chandler criterion, the occupancy? A layer carries none of that, and we
would end up with a layer full of ad-hoc metadata — the definition of a bad model.
Worse, the user could delete the shape inside and be left with a measurement that
has no line: the object's integrity evaporates.

**But the underlying observation is right, and it must be acted on.** Today there
are **three separate drawing engines**:

| domain | drawn by |
|---|---|
| shapes | ours (`shape-handlers.ts`, 572 lines) |
| annotations | ours (`annotation-handlers.ts`, 220 lines) |
| **measurements** | **Mol\* native** — `plugin.managers.structure.measurement.addDistance` (`measurement-handlers.ts:281`) |

and a naive Interactions domain would bring a **fourth**. That duplication is real
and must not grow.

#### The contract

A domain object (`Measurement`, `InteractionSet`, …) **owns** a visual realisation.
The realisation is therefore **selectable**, and the object survives changing it:

- **`renderer="native"`** — delegate to the engine that already does it well (Mol\*'s
  measurement manager; Mol\*'s `InteractionsShape`). Free, fast, with picking and
  well-placed labels. The control is exactly what that engine exposes — for
  interactions, three knobs per kind (`color`, `style`, `radius`); **not absolute**.
- **`renderer="primitives"`** — the realisation materialises as a layer of **owned**
  shapes + annotations: absolute control, at the cost of reimplementing billboard
  labels, dashes, picking, and of paying per primitive at scale.

**Consequence — and this is the point:** because the object *owns* rather than *is*
its realisation, the second renderer is purely **additive**. Tie the domain to
shapes on day one and we lose Mol\*'s native rendering, which is free and good.
Own the realisation and we lose nothing.

**Build `native` first. Declare `primitives`; do not build it** until a real user
needs per-edge colouring by occupancy or a distance label on every bond. Two
renderers are twice the maintenance and twice the bugs.

#### Mol\* offers far more native machinery than we use (2026-07-12 survey)

The `native` renderer is not a compromise — in every domain checked, Mol\* exposes
an inlet for **externally supplied data** and keeps its own engine optional:

| domain | what Mol\* offers | what we use today |
|---|---|---|
| **interactions** | `CustomInteractions` transformer — you hand it the edges (`{kind, a, b}` addressed by **`atom_index`**), it renders them natively. Its own `ComputeContacts` engine is a *separate, optional* inlet. | **nothing** — we draw pre-computed pairs as anonymous cylinder shapes |
| **annotations** | MolViewSpec (`extensions/mvs/components/`): `annotation-label` (`fieldName` picks the text column), `annotation-color-theme`, `annotation-tooltips-prop`, `annotation-structure-component`, and `custom-label` (`items: [{text, position}]`, position by *selection* **or** by explicit `x,y,z`). Addressed at any level — `whole_structure / entity / chain / residue / residue_range / atom` — with **`atom_index`** and **`residue_index`** among the fields, plus `group_id` to gather several rows under **one** label. | the basic `label` representation with `customText` |
| **measurements** | `plugin.managers.structure.measurement` | ✅ we use it |

So the answer to *"do we have to choose between their engine and our data?"* is
**no, in every case**: Mol\* consistently separates *what to draw* from *who
computed it*. Our data, their rendering.

**Two notes, deliberately not acted on:**

- **`annotation-color-theme` overlaps with our per-atom colour layers** (Contract B,
  `_atom_color_layers`) — we reimplemented something Mol\* already had. **Do not
  change it.** Contract B works and was validated in a real browser in Phase 14 of
  the rework; swapping it now is risk with no benefit. Recorded here because it is a
  ready-made escape route if the layer system ever hits a performance wall.
- **MVS annotations are designed for *declarative* views** (data loaded once from a
  CIF/JSON to describe a scene). Ours are **interactive and mutable** — added,
  retitled and deleted live. That the MVS provider accepts *inline* data and updates
  efficiently in flight is plausible (`MVSAnnotation.createEmpty(schema)` suggests
  programmatic construction) but **unverified**.

#### Decision (2026-07-12): the MVS annotation machinery is **post-1.0**

Deferred — the rationale, the risk and the deferred work live in
[`post_1.0/annotations_mvs_machinery.md`](post_1.0/annotations_mvs_machinery.md).
In short: it is not what blocks the user (the 1.0 Annotations subpanel needs
in-place text editing, renaming, layers and creation from the active selection —
none of which needs MVS), its interactive behaviour is unverified, and **Contract V
makes deferring free** because a renderer swap is additive once the object owns its
realisation.

**It does not touch Interactions**: `extensions/mvs/` and `extensions/interactions/`
are different extensions, and the `CustomInteractions` plan stands unchanged.

**One condition binds the pre-1.0 work**, and it is the only reason this contract
mentions it at all: **an annotation's anchor must be an extensible concept from the
start**, not "a list of atoms, forever". Today `Annotation.set_coordinates` raises
`NotImplementedError` ("annotation anchors are tied to atom indices"). If the model
and the serialisation treat the anchor as something *with a shape* — atoms today,
free coordinates or a residue/chain level tomorrow — MVS later arrives as an
additive extension. Close it as `atom_indices` and it arrives as a format migration.

#### Owned objects are not the user's objects

A realisation made of primitives introduces a distinction the codebase does not yet
have: **derived (owned) scene objects vs primary ones.** A shape that exists
*because a measurement needs it* is not a shape the user created, and it must not
appear in the Shapes panel cluttering it, nor be independently deletable.

There is an exact precedent: transient regions (`focus`, `orientation`, `plane`) are
already filtered out of the panel and of `export_state` by `_TRANSIENT_REGION_TAG`.
Generalise that mechanism rather than inventing a second one.

An owned primitive **does not serialise on its own** — it is rebuilt from its owner's
recipe, exactly as a dynamic region's `atom_indices` are (Contract R).

### Contract S5 — Every scene object serialises (extends Contract C)

The session document must carry, for each scene object: its creation recipe,
its **`hidden`**, and its **`layer_tag`**. In particular:

- The document grows a **`shapes`** key, sourced from `_shape_history`.
- `annotations` and `measurements` records grow `hidden`.
- The layer *groups* themselves (a group is more than the sum of the `layer_tag`
  of its members once it can be renamed and coloured) get a **`layers`** key.

`session_reproducibility.md` §"The rule for every future change" applies in
full: a round-trip test that asserts the **content** (the hidden flag survived,
the shape came back with its colour and radius), verified by mutation — not a
test that merely asserts the object exists after import.

**Version:** these are additive keys. A v2 reader that ignores them still works,
so this is a **v2 extension, not a v3**. But an old document (no `shapes` key)
must import cleanly as "no shapes", and that must be a test.

### Contract S6 — Scene objects enter the scene history (extends Contract H)

Creating, deleting, hiding, retagging, relayering or restyling a scene object is
a scene mutation and is recorded in the **single** scene history
(`@records_scene_history`), so it is undoable exactly like a region operation.

Rationale: the panels put a **trash button** on every row. A destructive,
one-click, GUI-native action that cannot be undone is not acceptable, and the
mechanism (snapshot-based undo) already exists and needs only to be applied.

Note the interaction with S5: snapshot undo is `export_state`-based, so **S6 is
not merely helped by S5 — it depends on it.** Until shapes are in the document,
undoing across a shape operation would silently delete the shapes. S5 must land
first, or the undo will eat them.

#### Continuous gestures must coalesce — **in the history, not in the GUI**

A slider drag (opacity, radius) or typing into a text field fires one mutation per
step. Each mutation is a full `export_state` snapshot. Two consequences, and the
second is the serious one:

1. Snapshotting the whole scene per mouse-move is **expensive**.
2. **It evicts the user's history.** The stack is bounded — `limit: int = 25`
   (`scene_history.py:45`) — so ~100 snapshots from one drag truncate to 25, and
   now *all 25 entries are that single drag*. Everything the user did before is
   gone. **This is not lag; it is losing the undo history**, and it is why the
   coalescing is mandatory rather than an optimisation.

**The mechanism belongs to the history, not to the panel.** A GUI-side debounce
would leave a plain Python loop (`for a in alphas: shape.set_alpha(a)`) evicting
the history just the same, and it would break the symmetry Contract S2 promises —
the GUI and the API must produce the same state, *including the same history*.

So: the history grows a coalescing window (a transaction, or a `coalesce_key` +
time window on `records_scene_history`). The GUI merely opens it on `dragStart` /
focus and closes it on `dragEnd` / `blur` / Enter. Python callers get the same
protection for free, and can open a transaction explicitly around a loop.

### Contract S7 — A damaged anchor is a *state*: never a silent deletion, never a stale number

§0.10 measured two opposite failures after an `apply_system_edit` that removes atoms,
and this contract answers both.

**1. An object whose anchor is destroyed must not be silently deleted.** Today it is
(`core.py:1928` returns `None` and the object vanishes). The user created it; removing
it on their behalf, without a word, is not "defensive" — it is losing their work.

- The object **survives**, carrying an explicit **`broken`** state and its reason
  (which anchor atoms are gone).
- It may become **valid again after an undo** — which is impossible if it was deleted.
- `broken` is part of the summary and **serialises** (S5).
- The panel row shows a **warning marker**, and nothing renders for it.

**2. An object whose anchor is *damaged* must not keep reporting its old value.** Today
it does: a centroid endpoint that loses one of its atoms is remapped, the centroid
moves, and **the stored `value` is not re-derived** — so the panel, the 3D label and
`info()` all report the previous number with complete confidence (§0.10b).

- A value is **derived from the recipe, at the current frame, over the atoms that exist
  now**. It is never a cached number outliving the atoms that produced it.
- Where it cannot be derived, the row shows `—`, never the last known number.

**A stale number is the single worst outcome in this codebase.** An error is loud, a
deletion is at least detectable, but a plausible wrong value propagates into a figure
and into a paper. This is the rule the panel designs and Phase 1's "re-derive, never
restore" both descend from.

This is the anchor's *shape* mattering: an anchor is a concept that can be valid,
damaged, destroyed — or, post-1.0, of another kind entirely
(`post_1.0/annotations_mvs_machinery.md`).

---

## 3. Non-goals

- **No new molecular-system editing.** These panels never mutate the structure;
  `apply_system_edit` is not in scope.
- **No new shape types.** The 14 that exist are enough to expose.
- **No custom-shape authoring GUI** (Bloque 4, deferred long ago). Stays
  deferred.
- **Sections** (`Section`, the clipping planes) are scene objects by class but belong
  to the Viewport panel's world, not to these four. **Out of scope — but not fine:**
  they do not serialise either (§0.11), so a clipping plane does not survive a
  save/reload. That is **declared debt**, inherited by whoever owns Viewport. Closing
  this block does **not** close `session_reproducibility.md`'s promise.
- **An `owner` field on scene objects** (so the panel can say `· from elasnetmt`).
  Cheap and useful, but it is new API surface and this block has enough (§0.12).
  Deferred on purpose.

---

## 4. How this will be tested

Same standard as the rework — a claim in a test name must be asserted, and every
mechanism must be verified by **mutation** (revert the mechanism, the test must
fail):

- **Python**: the summary records (content, not `isinstance(dict)`); the
  summary re-syncs after *indirect* mutations; the round-trip of `hidden`,
  `layer_tag` and the shapes; undo across each scene-object operation; an old
  (shape-less) document imports cleanly.
- **JS unit**: each new panel renders its summary, and each affordance
  dispatches the expected `panel_action` (never a direct `handleMessage`).
- **E2E, real browser** (`js/tests/e2e/`, the harness built in Phase 14): hiding
  a shape from the panel actually removes it from the Mol\* render tree **and**
  Python agrees it is hidden. This is the test that would have caught §0.2, and
  no unit test can.

A mechanical acceptance criterion, in the spirit of the Phase 12 brief:

```bash
# no panel may mutate runtime state directly
grep -n "handleMessage" molsysviewer/js/src/managers/viewer-controller.ts | grep -i "hide_layer\|show_layer"
# -> must not appear inside refreshAddonsPanel
```
