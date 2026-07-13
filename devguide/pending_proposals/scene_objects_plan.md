# Scene objects — implementation plan (Measures, Annotations, Shapes, Layers)

**Status:** proposed (2026-07-12). Governed by
[`scene_objects_contracts.md`](scene_objects_contracts.md), which is normative
for this work. Scaffolding: this document and the per-phase briefs are deleted
when the block closes, exactly as the scene-rework plan was.

**Working agreement** (unchanged from the rework):

- One phase = one brief = one commit. I write the brief, the collaborator
  implements, **I audit before the commit** — on the working tree, against the
  code, never against the brief or the report.
- Every fix is verified by **mutation**: revert the mechanism, its test must
  fail. A test that still passes under mutation is hollow and does not count.
- "Green" means **all** of it: `pytest` + `npm run test:js` +
  `npm run build:runtime` + `npx tsc --noEmit` (baseline: **zero** errors).
- `molsysviewer/viewer.js` is generated: **never hand-edited**, rebuilt as the
  last step after the final TS change.
- `sandbox/` and `devguide/course/` are the maintainer's area. Never touched.

---

## The shape of the problem

The rework fixed the structural half of the scene (whole, regions). The
non-structural half — the scene objects — is still on the pre-rework
architecture: **the frontend keeps its own copy of the state, rebuilt by
watching messages go by**, and the panels are three tabs sharing one 75-line
generic list.

So this block is not "add buttons". It is: *establish the same source-of-truth
discipline for scene objects that regions now have, close the serialisation and
undo holes that discipline exposes, and only then build the panels on top.*

**Phases 0–4 are the saneamiento; 5–8 are the content; 9 proves it on screen.** The
content phases are cheap **only because 0–4 went first** — a rich panel built on the
shadow state (and on an API where `shapes` cannot even `hide()`) would harden the
defect instead of removing it.

| phase | what | contracts |
|---|---|---|
| 0 | Identity, `TagsManager`s, API coherence | T, S0 |
| 1 | State: the restore path rebuilds the model | S5 |
| 2 | The source of truth (summaries) | S1, S2, S3 |
| 3 | Undo, and coalescing | S6 |
| 4 | Broken anchors | S7 |
| 5 | **Measures** subpanel | — |
| 6 | **Annotations** subpanel | — |
| 7 | **Shapes** subpanel | — |
| 8 | **Layers** subpanel | S4, S4b |
| 9 | Real-browser validation and corpus | — |

---

## Phase 0 — Identity and API coherence (Contracts T and S0)

**Goal.** The five scene managers drifted apart as they grew, and the scene has
no coherent notion of *identity*. Fix both **before** the panels are built on
them — a panel built on an inconsistent API bakes the inconsistency into the GUI,
which is how the Shapes panel ended up bypassing Python in the first place.

This phase is bigger than the four that follow it. It is also the only one that
cannot be done later.

### 0a. Identity: `(domain, tag)` (Contract T)

A tag is unique **within its domain**. `site1` may be a region, a shape, a
measurement and an annotation at once.

- **Five per-domain guards**, one per manager, replacing the two asymmetric ones
  that exist today. `regions` gains the guard it never had (today
  `regions.add(tag='x')` succeeds while a shape `x` exists).
- **Type the addressing on the wire**: `hide_layer` / `show_layer` /
  `delete_layer` / `set_layer_tag` carry the `kind`; `tagIndex`
  (`state-handlers.ts:120`) is keyed by `(kind, tag)`.
  **The kind already exists on both sides** — `SceneObject.kind` in Python,
  `layerMeta`/`registerTaggedRef(ref, tag, kind)` in the runtime. Use it; do not
  invent it.
- **Qualify `_scene_objects`** (one flat dict shared by four domains) and
  **`Layer.members`** (one dict mixing regions and scene objects). Under Contract
  T two members may share a tag and one would silently overwrite the other.
- **Rewrite `architecture.md` §Key invariants 1**, which currently asserts a
  global tag uniqueness that the code does not have and will not have.

**The risk is silent aliasing** in a half-done migration: any site still indexing
by a bare tag merges two objects with no error. **The mutation test is
mandatory**: create the same tag in two domains, mutate one, assert the other
does not move — and check the test fails when `kind` is dropped from the key.

### 0b. `TagsManager`, one per domain (Contract T)

The tag policy of a domain becomes an object instead of a scattering: today it
lives in six counters on the view, two asymmetric guards in `scene_registry.py`
and five `_next_*_tag()` helpers in `core.py`.

Each `TagsManager` owns the prefix, the counter, the domain's uniqueness guard,
and **the high-water mark, serialised with the session** — because today the
counters reset to zero on reload and the next auto-generated `measurement1`
collides with the imported one (§0.9). Only `regions` was ever fixed, and the fix
was never generalised.

**It must not keep its own list of live tags** — that would be a second source of
truth about what exists, and it will drift from the registry. It owns the naming
policy and *asks* the registry.

### 0c. API coherence (Contract S0)

- **`LayersManager` (new).** Layers is the only domain with no manager at all
  (`core.py:1706` returns the raw registry), so it has nowhere to hang a
  creation verb. Copy the `RegionsManager` mould — **a `dict` subclass** — so
  `view.layers['x']`, iteration and `len()` keep working untouched, and give it
  **`.add(tag)`** (the house verb; never `new()`), plus the canonical surface.
- **Retire `view.new_layer()`** (`scene_registry.py:138`) in favour of
  `view.layers.add()`. It is the last survivor of the pre-Phase-13 style that
  `view.new_region()` → `view.regions.add()` already retired. Deprecate, migrate
  `docs/`, remove.
- **`tags` becomes a method everywhere.** It is a *property* in `selections` and
  `annotations` and a *method* in the other three, so `view.annotations.tags()`
  raises `TypeError: 'list' object is not callable`. **Breaking change,
  accepted** (pre-1.0): migrate `docs/` in this same phase.
- **Complete the `shapes` manager**: `count`, `records`, `delete`, `set_tag`,
  `show`, `hide` — it is missing all six, while annotations and measurements
  have them. This is the gap that made the Shapes panel reach past the API.

**Acceptance.** The canonical-surface table in Contract S0 is fully green, and a
test asserts it by introspection (so the next manager cannot drift back out).

## Phase 1 — State: the restore path must rebuild the model (Contract S5, §0.8, §0.9)

**Goal.** Close the reproducibility hole *before* anything is built on top of the
model, because today **a reload destroys it**.

`import_state` re-sends the raw creation messages to the frontend
(`state.py:148-156`) instead of going through the managers, so the Python objects
are never reconstructed. After a reload the measurement is **drawn on the canvas**
but `tags()` returns `[]`, `count()` returns `1` (they contradict each other),
`info()` reports it hidden, and `hide()` / `delete()` raise. See Contract §0.8 —
this was verified by execution, not inferred.

- **`import_state` rebuilds through the managers** (`measurements.add_distance(…)`,
  `annotations.add_annotation(…)`, …) — the same public path a user takes. This is
  Contract S2 applied to deserialisation: *the restore path may not reach past the
  public API either.*
- **`export_state` grows a `shapes` key** (source: `_shape_history`, already
  replayable) and a **`layers`** key; `annotations` and `measurements` records grow
  **`hidden`**. An old document with no `shapes` key must import cleanly as "no
  shapes" — additive keys, so this stays **v2, not v3**.
- **The tag high-water marks are serialised** for every domain (§0.9), via the
  `TagsManager` of Phase 0.
- **Backward compatibility, with safe defaults**: a v2 document with no `shapes`
  key loads as "no shapes"; a record with no `hidden` loads as visible; missing
  high-water marks fall back to the current counters (never to zero, or the next
  auto-tag collides with an imported one).
- Round-trip tests asserting **content** (the shape came back with its colour and
  radius; the hidden annotation came back hidden; the model is usable — `hide()`
  works after a reload), each verified by mutation.

> ⚠️ **Tolerant parsing is the easy half, and it is not this phase.** Defaulting a
> missing key does not rebuild anything. If the only thing that lands is safe
> defaults, `import_state` still leaves every measurement and annotation in the
> zombie state of §0.8 — drawn, uncountable, unhidable. **The phase is done when
> `view.measurements.hide(tag)` works after a reload**, not when the parser stops
> raising.

**Why this moved ahead of the summary.** The authoritative summary (Phase 2) is
computed *from the Python model*. Build it first and you get a panel that empties
itself the moment the user reloads a session, while the canvas still shows the
objects. And snapshot **undo is an `import_state`** — see Phase 3.

Read [`session_reproducibility.md`](../session_reproducibility.md) before
starting. This phase is that document's standing rule being enforced.

## Phase 2 — The source of truth (Contracts S1, S2, S3)

**Goal.** Python computes and pushes an authoritative summary of every scene
object; the frontend deletes its shadow state; every mutating affordance goes
through the public API. **The panels look exactly the same afterwards** — this
phase is deliberately invisible, so the plumbing can be verified in isolation.

- **Python.** A `_<domain>_summary_records()` + `_sync_<domain>_summaries_runtime()`
  pair per domain (ops `set_measurement_summaries`, `set_annotation_summaries`,
  `set_shape_summaries`, sent with **`_send_runtime_only`**), built on the `info()`
  each manager already exposes. **One op per domain, not one lump**: a trajectory
  frame change invalidates only the measurement values, and a combined op would
  re-push every shape and annotation on every frame — this repo has paid a
  ~3-second-per-message toll once already. Re-synced from **every** mutation,
  including indirect ones (a layer hide that hides its members; the rebuild after
  `apply_system_edit`).
- **Python.** `panel_action` handlers for the affordances the three panels
  already have: toggle visibility, delete, focus.
- **TS.** Delete `addonsAnnotations` / `addonsMeasurements` / `addonsShapes`
  (`viewer-controller.ts:562-564`) and every site that populates them; feed the
  panels from the summary. Route the eye through `onAction`, not
  `handleMessage` (`:2910`, `:2934`, `:2958`).
- **Keep in the frontend:** `addonsActive` (which row is selected) is *UI* state,
  not scene state. It stays. Do not over-migrate.
- **Re-send every new summary on `ready`** (`core.py:789-790`). A summary is
  `_send_runtime_only`, so it never enters `_message_history` and a frontend that
  attaches later never gets it by replay. Forget this and the panels are **empty in
  the popup, in a re-attached widget, after a kernel rebuild and in the standalone
  host** — while the canvas shows the objects. It will look perfect in the notebook
  it was written in and be broken everywhere else. **Test it with a fresh frontend.**

- **Split the action dispatcher — and for the right reason.** `viewer/core.py` is **3.244
  lines** and its `interaction_context_action` handler is a single `if/elif` chain with
  **53 branches**. Phases 5–8 add roughly **30 more**.

  **The reason is not performance.** Measured: the 53-branch chain costs **880 ns** in its
  worst case, and the action it dispatches then runs an `export_state()` snapshot (1–10
  **ms**) and a MolSysMT query. The dispatch is ~10.000× cheaper than the work behind it.
  Refactoring for speed here would be optimising 0,01%.

  **And `match/case` is not the fix**: measured at **874 ns** — CPython does not compile it
  to a jump table, it does the same sequential comparisons. It would be a monolith of 914
  lines with nicer syntax, still untestable in parts. It would *feel* like a fix.

  **The real reason: an action with no handler fails silently.** The chain ends **without
  an `else`** — after the last `elif action == "export_html"` comes the `except`. A missing
  handler does *nothing*: no error, no log, no trace. The panel button is simply dead, and
  says nothing. With ~30 new actions arriving, that is thirty chances to ship a dead
  button.

  A **`{action → handler}` table**, one module per domain, buys the thing the chain makes
  impossible — **a completeness test against the closed `PanelAction` union**
  (`js/src/ui/panels/types.ts:19`):

  ```python
  assert set(PANEL_ACTIONS) == set(HANDLERS)   # no action without a handler, no orphan handler
  ```

  That turns "I forgot the handler" from a silent production bug into a **red test**. It is
  also 5,7× faster (153 ns), which is the least interesting thing about it.

  Scope: **the dispatcher only** — not `core.py` at large. Retrofitting it in Phase 8, with
  all 30 branches already written, is a much worse trade.

**The trap.** `setLayerObjects` is fed from the same three maps. The Layers panel
will go blank if the summary does not also serve it.

**Acceptance.** Hiding an annotation from the panel makes
`view.annotations.info(tag)['visible']` false in Python. Today it stays true —
that is the mutation test.

## Phase 3 — Undo (Contract S6)

**Goal.** `@records_scene_history` on the four domains, so that deleting a
measurement — a one-click, destructive, GUI-native action — is undoable, like
every region operation already is.

**It depends on Phase 1, and the dependency is not tidiness — it is safety.**
Snapshot undo *is* an `export_state` / `import_state` cycle. Applied to the code
as it stands today, that means:

- undoing across a shape operation would **silently delete every shape** (they are
  not in the document — §0.3);
- undoing anything at all would leave every measurement and annotation in the
  **zombie state** of §0.8 — drawn on the canvas, absent from the model,
  impossible to hide or delete.

So shipping this phase before Phase 1 would not be merely useless: it would be
**actively destructive**. Phase 1 first, without exception.

**Also in this phase: coalescing (Contract S6).** The undo stack is bounded at 25
(`scene_history.py:45`), so a single slider drag — one snapshot per mouse-move —
**truncates the stack to 25 entries that are all that one drag**, wiping everything
the user did before. That is not lag; it is **losing the history**.

The coalescing window lives **in the history, not in the GUI**: a Python loop
(`for a in alphas: shape.set_alpha(a)`) must be protected too, and a GUI-only
debounce would break the symmetry Contract S2 promises. The panel merely opens the
window on `dragStart`/focus and closes it on `dragEnd`/`blur`/Enter.

## Phase 4 — Damaged anchors (Contract S7)

An `apply_system_edit` that removes atoms fails in **two opposite ways**, both measured
by execution (§0.10) and both silent:

- **The object is deleted.** An endpoint that loses *all* its atoms makes the whole
  measurement vanish (`core.py:1928` returns `None`). Same for an annotation. The user
  edits their system and **loses work**, with no warning.
- **Or it survives with a stale number.** A centroid endpoint that loses *some* of its
  atoms is remapped — but the stored `value` is **not re-derived**, so the panel and the
  3D label keep reporting the previous number **computed from an atom that no longer
  exists**. Measured: identical value before and after, and now wrong.

The fix, both halves:

- Post-edit validation marks the object **`broken`** (with its reason) instead of
  deleting it. It survives — and may become valid again after an undo.
- **The value is re-derived from the recipe**, never carried over. Where it cannot be
  derived, the row shows `—`.
- `broken` is part of the summary and **serialises**.

**A stale number is the worst outcome in this codebase**: an error is loud, a deletion is
at least detectable, but a plausible wrong value ends up in a figure.

## Phase 5 — Measures subpanel

The first real panel. `MeasuresPanel` replacing the generic list:

- **The value, with units** (`5.93 Å`, `112.4°`) — today the row says *"2 picks"*
  while `value` is already in the message and gets thrown away.
- Kind, endpoints and their labels, endpoint policy.
- **The series over the trajectory** (`measurements.series(tag)`) — the natural
  content of this panel on a dynamic system.
- Create a distance/angle/dihedral **from the active selection**.
- Rename, layer, show/hide, delete.

## Phase 6 — Annotations subpanel

- **Edit the text in place** (`set_text`) — the panel has no edit affordance at
  all today.
- Kind, anchor, atom count; re-anchor (`set_anchor` / `set_group_index`).
- Create from the active selection; rename, layer, show/hide, delete.
- Build on `add_annotation`, **not** on the deprecated `add_label`.

## Phase 7 — Shapes subpanel

- Kind and geometry summary per shape (`shapes.info()` is already panel-ready).
- **The style mutators**: colour, alpha, radius/radii, scales — none reachable
  from the GUI today.
- **`render_status()`**: whether a trajectory-bound shape resolved on this frame.
  A Shapes panel that says nothing when a shape fails to render is hiding the one
  thing the user needs. A warning icon on the row, and a tooltip with the actual
  cause (*"invalid coordinates at frame 42"*).
  **It is runtime-only by design** (its own docstring: not part of the reproducible
  scene history) — so it is a **diagnostic, not scene state**. It lives in the
  frontend and **must not travel in the Python summary**. Contract S1 governs scene
  state, not runtime diagnostics.

## Phase 8 — Layers subpanel

The current panel assigns a region to a layer by **typing both tags into two text
boxes**, and disables "Remove" for scene objects with a tooltip that says they
*"are managed by their own addon layer tags"* — **which is false**:
`Layer.detach(obj)` exists and works.

- **`LayersManager` (new).** Layers is the only domain with no manager:
  `view.layers` returns the raw registry (`core.py:1706`), so there is nowhere to
  hang a creation verb. Give it the manager every other domain has, copying the
  `RegionsManager` mould (**a `dict` subclass**, so `view.layers['x']`, iteration
  and `len()` keep working untouched), with **`.add(tag)`** — the house verb
  (Contract S4b), not `new()`.
- Create, rename (`Layer.set_tag`), delete a layer. Mind the invariant this
  breaks: the model currently **deletes any layer that becomes empty**
  (`scene_registry.py:80-81`), so a user layer must be told apart from a
  degenerate auto-layer or it will evaporate before its first member arrives.
- **The mechanism is `Layer.provenance = "auto" | "user"`** (Contract S4b): an
  object's own shadow layer is `auto`; a layer the user creates is `user`; adding a
  further member **promotes** `auto` → `user`; on becoming empty, only `auto` is
  deleted. No demotion.
  Two things it must not forget: **`provenance` serialises** (or every layer is
  reborn `auto` on reload and the user's empty layers evaporate one round-trip
  later), and **promotion must cover regions**, which carry membership in
  `region.layer` and not in `layer_tag` — the asymmetry that has already orphaned
  regions once.
- Assign/detach **both** kinds of member — and mind Contract S4: regions carry
  membership in `region.layer`, scene objects in `obj.layer_tag`. Writing the
  wrong field silently orphans the member; that is a defect this repo has already
  shipped once.
- Group visibility; per-member state.
- **Filter out the degenerate auto-layers.** Every loose scene object carries
  `layer_tag == tag`, and `buildLayers()` groups by any non-empty layer tag — so
  three unrelated spheres today render as three one-member "Layer Groups" and the
  tab badge counts them. A group is a *user-made* grouping.

## Phase 9 — Real-browser validation and corpus

- E2E against real Mol\* on the harness built in Phase 14 of the rework
  (`js/tests/e2e/`): hiding a shape from the panel actually removes it from the
  **Mol\* render tree**, and Python agrees. This is the test that would have
  caught the §0.2 defect, and no unit test can.
- Migrate `docs/` for whatever public API changed (**not** "little to none": Phase 0
  breaks `tags`, retires `view.new_layer()`, and Contract T changes what a tag
  means).
- Promote `scene_objects_contracts.md` into `scene_contracts.md` and delete this
  plan and the briefs.

---

## What is explicitly not in this block

- New molecular-system editing (`apply_system_edit` is not in scope).
- New shape types — the 14 that exist are enough to expose.
- Custom-shape authoring GUI (Bloque 4): stays deferred.
- `Section` / clipping planes: scene objects by class, but they belong to the
  Viewport panel's world. **Out of scope — and broken:** they do not serialise either
  (§0.11), so a clipping plane does not survive a save/reload. **Declared debt**,
  inherited by whoever owns Viewport. Closing this block does not close
  `session_reproducibility.md`'s promise.
- An **`owner`** field on scene objects (so a row could read `· from elasnetmt`).
  Add-on shapes are ordinary shapes — they are created through the public API
  (§0.12) — so the Shapes panel **will show them and let the user delete them**, which
  is correct: it is the user's scene. Two consequences are accepted rather than
  discovered: an add-on must tolerate its shape being deleted (its handle goes
  `_active = False`), and the panel cannot yet say where an object came from. The
  `owner` field is cheap and useful and is **deferred on purpose** — it is new API
  surface and this block has enough.
- **Re-rendering measurements with owned primitives** (Contract V). They are drawn
  by Mol\*'s native measurement manager and stay that way for now: the refactor has
  guaranteed visual regression and no user-visible benefit. Revisit once
  Interactions has proven the model.
- `sandbox/Curso/`: still on the pre-rework API, deliberately, and it is the
  maintainer's call — not this block's.

## `viewer/core.py` — what this block takes out of it, and what it deliberately leaves

Measured 2026-07-12:

| | |
|---|---|
| `core.py` | **3.244 lines — 37% of the whole `viewer/` package** (8.801) |
| next biggest file | `regions.py`, 965 lines — **`core.py` is 3.4× larger** |
| methods | **109**, of which **68 are "miscellaneous orchestration"** |
| the event dispatcher | **a single method of 914 lines** (774–1687): one `if/elif` chain, **53 branches** |

The problem is not the line count. `viewer/` is **already split into mixins** — `camera`,
`export`, `history`, `load`, `regions`, `state` — and each has a subject. **`core.py` is
what was left over.** It is a drawer, not a module.

### The rule: split what we are going to touch, not what offends the eye

A refactor is justified by the work it enables, not by aesthetics. Rearranging 3.244 lines
with no defect driving it is how things get broken — the rework's lesson was that
"tidying" changes, with no concrete failure behind them, are the ones that introduce bugs.
This block already has ten phases and two dangerous ones.

**So two things come out, both as a side effect of work this block must do anyway:**

- **The action dispatcher → Phase 2.** Phases 5–8 add ~30 branches to a chain that already
  has 53. Leaving it alone is not neutral: **it makes it 60% worse**. In Phase 2, where the
  first new handlers land, it becomes a **`{action → handler}` table with one module per
  domain**. Scope: **the dispatcher only** — not `core.py` at large. If the diff touches
  anything else in that file, it has gone out of bounds.
- **The five `_next_*_tag()` generators → Phase 0**, because the `TagsManager` takes them.

That is roughly a thousand lines leaving `core.py` without a single line of refactoring
done "for cleanliness".

### Declared debt: the eight `_remap_*` methods are in the wrong file

`_remap_indices`, `_remap_atom_pairs` and six siblings live in `core.py` — while
**`viewer/index_mapper.py` already exists** (252 lines) and is exactly their home.

**They stay put.** They work, nothing in this block touches them, and moving them would be
a change with no failure behind it. Written down here so it is **declared debt with its
home already identified**, and not a thing nobody ever noticed.

## What comes after this block

[`interactions_domain.md`](interactions_domain.md) — a fifth scene domain
(hydrogen bonds, disulfide bridges, π-stacking…), assessed on 2026-07-12 and
**approved in principle**. It inherits every contract established here (T, S0, S1,
S5, S6, V) and would have to be rebuilt if attempted first.

That a whole new domain drops into this architecture **without bending anything**
is the best evidence available that the design of this block is right.
