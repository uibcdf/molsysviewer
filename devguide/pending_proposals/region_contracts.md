# Region contracts (normative)

**Status:** proposed (2026-07-10) — **not implemented**. Execution order, gates and audits live
in `scene_master_plan.md`. Promote this file to `devguide/` once its contracts are implemented
and guarded by tests.

**No external users.** `sandbox/Curso/`, `docs/` and `bloques.md` are provisional and are
regenerated in master-plan Phase 10. Breaking changes are allowed and expected; they are
declared in §Migration with **no shims and no deprecation period**.

**Scope:** the three contracts that govern how a **region** relates to the
**whole**, to **colour**, and to **persisted state**. They are not specific to
the Studio → Regions subpanel: they bind the public Python API, the JS↔Python
protocol, `whole`, `styles.focus()`, `new_view`, `tools.basic.extract/merge`,
and every future surface.

They exist because the codebase currently has **two disagreeing sources of
truth** about what is being painted, and no notion of colour ownership. Both
defects are invisible from Python and invisible from the tests, which assert
emitted messages rather than rendered effects.

---

## 0. Why these contracts exist (evidence)

Three defects, verified in code, all downstream of a missing contract.

### 0.1 "No representation" does not exist in the frontend

`js/src/managers/handlers/state-handlers.ts`, in **both** `createRegion` and
`setRegionRepresentation`:

```ts
const reprType = msg.representation ?? "cartoon";
```

Every region — including one created by `view.new_region("protein")` with no
representation — receives its own `cartoon`. Meanwhile Python believes the
opposite (`viewer/regions.py`, `_region_has_visible_representation`):

```python
return (
    bool(getattr(region, "_active", False))
    and not bool(getattr(region, "_hidden", False))
    and (
        region.representation is not None
        or region.preset is not None
        or bool(region.repr_params)
    )
)
```

Consequences, all real and all shipped:

- `Region.reset_representation()` does **not** restore the base look; it turns
  the region into a `cartoon`.
- The opacity slider is inert on a "Base" region (Python guards) even though
  Mol\* is painting a `cartoon` that *could* be made translucent.
- **Overlap detection is blind.** A region with no explicit representation is
  painted and can z-fight, yet Python excludes it from
  `_overlapping_visual_region_tags`, so the ⚠ badge never appears.
- `tests/regions/test_region_flow.py::test_region_reset_representation_restores_base_visual_state`
  passes while asserting only the emitted message dict. Its name claims a visual
  outcome it never checks.

### 0.2 Colour has no owner

`viewer/core.py` holds a single canvas-wide `_atom_color_map: dict[int, int]`.
The protocol has only `set_atom_colors` (whole map, `replace` flag) and
`clear_atom_colors` (no arguments). Therefore a colour "belonging to a region"
is not representable. `Region.reset_colors()` (`regions.py`) and
`Whole.reset_colors()` (`whole.py`) have **byte-identical bodies**:

```python
self._view._atom_color_map.clear()
self._view._send({"op": "clear_atom_colors"})
```

So "reset the colours of this region" wipes the whole canvas, and
`Region.set_color_by_values(replace=True)` replaces the canvas map from a
region's scope.

### 0.3 Per-atom colour destroys the structural theme

`js/src/managers/handlers/state-handlers.ts`:

```ts
async clearAtomColors(_msg: ClearAtomColorsMessage) {
    clearPerAtomColors();
    await this._applyPerAtomColorTheme();   // ← re-applies msv-per-atom on an empty map
}

private async _applyPerAtomColorTheme() {
    const components = this.callbacks.getComponents();   // ← ALL components
    await this.plugin.managers.structure.component.updateRepresentationsTheme(
        components, { color: MsvPerAtomColorThemeName as any },
    );
}
```

and `js/src/themes/per-atom-color.ts`:

```ts
const DEFAULT_COLOR = Color(0xaaaaaa);
…
return c !== undefined ? Color(c) : DEFAULT_COLOR;
```

Two consequences, both visible on screen and neither tested:

- **`reset_colors()` paints the system uniform grey.** Its docstring promises to "revert to
  the current representation theme". It clears the map and then re-applies the per-atom theme
  over an empty map, so every atom resolves to `0xaaaaaa`.
- **Colouring one region greys out everything else.** The per-atom theme is applied to *all*
  components, and any atom absent from the map falls to `DEFAULT_COLOR`.

The per-atom theme is a **replacement** for the structural theme, when it must be a
**decorator over it**: an atom with no colour in any layer has to fall through to whatever
theme the representation would otherwise use.

### 0.4 The whole's colour theme lives in the frontend, in another subpanel

`js/src/managers/viewer-controller.ts:975-980` wires the **System** subpanel's *Colour scheme*
dropdown straight to Mol\*:

```ts
const themeName = scheme === "physicochemical" ? "msv-physicochemical" : "element-symbol";
await this.plugin.managers.structure.component.updateRepresentationsTheme(components, {
    color: themeName as any
});
```

The whole's structural colour theme is therefore: (a) not in the Python API at all, (b) not
serialised, (c) owned by a subpanel that is not `Whole`, and (d) silently clobbered by any
per-atom colouring (§0.3). See `studio_whole_subpanel.md`.

### 0.5 A region serialises its identity, not its state

`viewer/state.py`:

```python
regions.append({"tag": tag, "atom_indices": list(region.atom_indices)})
```

Representation, preset, params, visibility, defining expression, colours and
provenance are all lost. `import_state` recreates naked regions. The
transient-tag filter (`_TRANSIENT_REGION_TAG`) is applied in
`_region_summary_records` but **not** on export, so a `focus3` produced by
`styles.focus()` is exported and reimported as a permanent, manageable region.
The `whole`'s own representation is not exported either.

---

## Decision 2 — exclusive atom ownership: **ADOPTED** (2026-07-10)

**Status: CLOSED.** Gate passed at master-plan Phase 1. Contracts A and B below were written for
the *previous* model (the whole paints everything; regions paint on top). The clause replacements
in §*Clause replacements* are **now in force**, and the three requirements in §*Requirements* are
part of the contract, not advisory notes.

**The model.** Each atom has exactly one visual owner: the topmost visible region that draws it
**opaquely**, else the `whole`. The whole masks its owned atoms to full transparency, **on its own
component only**, and never rebuilds its component.

> ### ⚠ Corrected 2026-07-10 — how ownership is *realised* is not settled, and an earlier draft
> of this section prescribed the wrong mechanism.
>
> This section used to say: *"the `whole`'s Mol\* component is built as the complement of owned
> atoms."* **That prescription was wrong and has been withdrawn.** Phase 1's first benchmark
> implemented it faithfully and measured, at n = 95,000 with a live rasteriser, **1,029 ms per
> region visibility toggle** — of which **906 ms was `addRepresentation` alone**, i.e. rebuilding
> the whole's mesh. The other three stages (`buildSelectionFromAtomIndices`,
> `Bundle.fromSelection`, the `StructureComponent` commit) summed to 14 ms. The benchmark
> measured the cost of that one implementation, not the cost of ownership.
>
> **The viewer already masks atoms without rebuilding anything.** `applyVisibility()` in
> `js/src/managers/handlers/state-handlers.ts` ends with
> `setStructureTransparency(this.plugin, components, 1, async () => loci)` — full transparency
> over the hidden atoms, on the components that already exist. It backs `update_visibility`, and
> therefore `view.isolate()` and `region.show_only()`.
>
> Measured on the same machine, harness and structure, ten toggles alternating an 85,500-atom
> mask at n = 95,000:
>
> | mechanism | rasteriser paused | rasteriser live |
> |---|---:|---:|
> | rebuild the whole's component | 923.1 ms | 1,029.5 ms |
> | **mask via per-atom transparency** | **12.1 ms** | **9.2 ms** |
>
> Two orders of magnitude, and below the 150 ms threshold. The mask mechanism is therefore the
> candidate implementation, and the decision rule below must be applied to **its** numbers.

**What it would buy.** Z-fighting becomes impossible rather than merely warned about. Colour
precedence and render order collapse into one `order` per region instead of two counters that can
desynchronise. `show_only` becomes ownership rather than a special case. And §B.4's question —
*what lies beneath a region's own colour layer* — answers itself: the owner's own structural theme.

Note the corrected claim: masking removes **duplicated drawing**, not **duplicated geometry**.
The whole's mesh still contains the owned atoms, fully transparent. Z-fighting disappears because
only one surface draws opaquely; memory does not drop. An earlier draft of this section claimed
"no duplicated geometry". It is wrong.

**What it would cost — still open, and blocked on one design question.**
`setStructureTransparency` is called today with `getComponents()`, i.e. **every** component of the
structure. If the region components are among them, the same atom would be faded inside the region
as well, and ownership would be unimplementable by this route without **per-component
transparency**. That question must be answered before the numbers mean anything. The mask cost
must also be measured at 10%, 50% and 90% ownership fractions: transparent geometry still costs
fill and sorting, and the 9.2 ms above is a 10% measurement.

**A further constraint on any mask-based implementation.** `currentVisibleIndices` is a single
global visibility set already owned by `view.show/hide(selection)` and Python's `atom_mask`. An
ownership mask must **compose** with the user's mask, not overwrite it.

### The result (Phase 1, measured on a clean post-toll baseline)

The decision rule, fixed in advance, was: **< 150 ms** per region visibility toggle at
n = 95,000 ⇒ adopt fully; 150–500 ms ⇒ adopt with a deferred rebuild; **> 500 ms** ⇒ ownership
between regions only.

| n = 95,000, rasteriser live | per-toggle |
|---|---:|
| mask, 10% owned | 14.1 ms |
| mask, 50% owned | 26.4 ms |
| mask, 90% owned | **32.1 ms** |
| *(reference)* rebuild the whole's component, 10% owned | 1,052 ms |
| *(control)* today's `setSubtreeVisibility` | 0.1 ms |

Worst case **32 ms**, a factor of five under the threshold. **Adopt fully.**

The benchmark asserts the invariant before it times anything: the whole's component carries a
transparency layer of value `1` over *exactly* the owned atom set, and the region's component
carries none. Two earlier attempts were rejected — the first measured a component rebuild
(`addRepresentation` was 906 of 923 ms, so it measured mesh generation, not ownership); the second
passed `getComponents()`, which **includes the region's component**, so it faded the region rather
than the whole.

**Picking is safe, and this is verified in Mol\*'s source.** `mol-gl/renderer.ts` defines
`pickingAlphaThreshold: PD.Numeric(0.5, …)` — *"The minimum opacity value needed for an object to
be pickable."* A masked atom has effective alpha 0 and is discarded by the pick pass. Probed on all
three cases, through the viewer's own hover/click/context-menu paths:

| case | result |
|---|---|
| owned atom, region visible | picks the **region** |
| unowned atom | picks the **whole** |
| owned atom, region hidden, mask applied | picks **nothing** |

### Requirements (in force, not advisory)

**R-O1 — Ownership is by opaque drawing.** The whole masks a region's atoms **only if that region
draws them opaquely**, i.e. its effective `alpha` reaches `pickingAlphaThreshold`. A translucent
region does **not** take ownership of drawing: the whole keeps painting beneath it, which is
exactly what translucency promises, and stays pickable.

Without this clause, exclusive ownership **breaks the opacity slider**. A region at `alpha = 0.3`
would reveal emptiness instead of the structure behind it, and its atoms would be simultaneously
unpickable in the region (below threshold) and unpickable in the whole (masked to alpha 0) — an
atom both invisible and unclickable. Blending between a translucent surface and what lies behind it
is not z-fighting; it is what the user asked for.

**R-O2 — The mask is updated by deltas**, never recomputed in full. Contract R's `dynamic` regions
re-evaluate their atom set per frame; a full mask recompute costs 26 ms at 50% ownership and the
frame budget is 16 ms (`message_toll_performance.md` §5.1).

**R-O3 — The ownership mask composes with the user's mask.** `currentVisibleIndices` is a single
global visibility set already owned by `view.show/hide(selection)` and Python's `atom_mask`. The
ownership mask must compose with it, never overwrite it.

**R-O4 — `pickingAlphaThreshold` is not lowered to 0** by the viewer. At 0, a masked whole becomes
pickable again and ownership silently breaks.

### Clause replacements (now in force)

The clauses written in Contracts A and B below describe the *previous* model. Where this table
disagrees with them, **this table wins**. Read it before implementing §A or §B.

| Clause | Previous model | **In force under exclusive ownership** |
|---|---|---|
| §A.2 rule 2 (state **None**) | region has a component but no representation child; the whole paints its atoms | unchanged |
| §A.3 (`hide()` on state-**None**) | no-op that warns | unchanged — a region that owns nothing has nothing to hide |
| §A.4 (`show_only`) | delegates to `view.isolate`, reshapes the whole | becomes pure ownership: the region takes every atom; no `isolate` call |
| §B.2 (precedence) | region layer beats base layer | **subsumed**: an atom's colour is its owner's, full stop |
| §B.4 (§ *what lies beneath*) | four-level resolution order | collapses to two: owner's layer, then owner's structural theme |
| §B.5 (decorator theme) | required | still required, but only over the owner's own theme |
| Overlap ⚠ badge | the only answer to z-fighting | becomes **informational**: z-fighting is impossible |
| Whole's Mol\* component | all atoms, all drawn | all atoms, with those owned by visible regions **masked to full transparency** on the whole's component only. The component is **not** rebuilt. Geometry stays; drawing does not. |

One row is **not** replaced, and it is the subtle one. A region that draws **translucently** owns
nothing (R-O1). For its atoms, the whole keeps painting, the four-level resolution of §B.4 still
applies, and the ⚠ badge still means something. Ownership governs opaque drawing; translucency is
the explicit request to see what lies beneath.

---

## Contract A — A region's representation is genuinely optional

### A.1 Three explicit states

A region is in exactly one of three states. The state is **named**, never
inferred from whether a params dict happens to be empty.

| State | Requested as | Own Mol\* component | Whole hidden ⇒ |
|---|---|---|---|
| **None** (no own visual) | `set_representation(None)` · `reset_representation()` | no | invisible |
| **Inherit** | `set_representation("inherit", **params)` | yes, using the whole's **live** representation type | **visible** |
| **Own** | `set_representation("cartoon", …)` · `preset=…` | yes | visible |

`"inherit"` is a reserved representation name. It is not a Mol\* type and must
be rejected by `_normalize_representation_type` as a *type* while being accepted
as this sentinel.

### A.2 Rendering rules (frontend)

1. The frontend **never invents a representation type**. The two
   `?? "cartoon"` fallbacks are removed.
2. State **None** ⇒ the region has a Mol\* *component* (needed for `focus` and
   for index bookkeeping) but **no representation child**. Those atoms are
   painted by the whole's representation, if the whole is visible.
3. State **Inherit** ⇒ the region gets its own representation whose *type* is
   the whole's current type (or preset), with the region's own `params`
   (`alpha`, `quality`, colour theme) applied on top.
4. **Live tracking.** When `set_global_representation` changes the whole's type,
   every region in state **Inherit** is repainted to follow it. This is a new
   edge in `StateHandlers` and must be covered by a unit test.
5. State **Own** ⇒ unchanged from today's behaviour, minus the fallback.

### A.3 Visibility

Representation inheritance is **not** visibility inheritance. A region in state
**Inherit** or **Own** has its own component and can be shown, hidden, isolated
and focused independently of the whole.

A region in state **None** has nothing of its own to hide. `Region.hide()` on it
is a **no-op that must warn**, and the GUI disables the control with a tooltip.
Hiding such a region "for real" would require subtracting its atoms from the
whole's component — a larger redesign, explicitly **out of scope** (§Deferred).

### A.4 Operations that assume an own visual

> **Superseded in part by Decision 2.** `show_only()` becomes pure ownership and no longer
> delegates to `view.isolate`. See the clause-replacement table above.

`show()`, `hide()`, `show_only()` and the style composer all act on a region's own
representation. On a state-**None** region:

- `show()` / `hide()` are **no-ops that warn** (§A.3).
- `show_only()` (isolate) delegates to `view.isolate(selection=atom_indices)`, which acts on
  the whole rather than on the region's component. It therefore **still works** in state
  **None** — it is the one visibility operation that does — because it reshapes what the whole
  paints. This asymmetry must be documented in the GUI, not hidden: `Isolate` stays enabled,
  `Hide` does not.
- `set_representation(alpha=…)` without a type is meaningless; the caller wants `"inherit"`.

### A.5 Transient regions

`styles.focus()`, `show_orientation_axes()` and `show_best_fit_plane()` register `Region`
objects (`focus<n>`, `orientation-region<n>`, `plane-region<n>`), matched by
`_TRANSIENT_REGION_TAG`. They are exempt from this contract's GUI rules: never listed, never
serialised (§C.2), never counted for overlap, never given a colour layer (§B.6).

At rest they are all in state **Own**. `styles.focus()` passes a representation to
`new_region` directly (`styles.py:642-648`, and it raises without one). The geometry overlays
create the region first and call `set_representation("orientation" | "plane", …)` immediately
after (`viewer/regions.py:455-462, 488-495`), so they pass transiently through state
**None** — which under this contract means one fewer wasted Mol\* rebuild, since the creation
no longer paints a `cartoon` that the next call immediately tears down.

### A.6 Python must describe reality

`_region_has_visible_representation()` becomes true exactly when the region has
an own representation (states **Inherit** and **Own**) and is not hidden. With
that, overlap detection reports what Mol\* actually paints, and the ⚠ badge
starts working for the first time.

### A.5 Callers that hand-roll inheritance today

`new_view.py:118-125` hides the whole, creates the region, then **copies the
whole's representation onto it by hand**, falling back to preset `auto`.
`tools/basic/extract.py:65` and `tools/basic/merge.py:123` follow the same
pattern. All three become `set_representation("inherit")` and gain live tracking
they do not have today (they copy a snapshot and never notice later changes to
the whole).

This is why the `whole`-hidden case is not an edge case: it is the canonical
entry point of `new_view(selection=…)`. A GUI-created region defaulting to
state **None** while the whole is hidden would be silently invisible; the
Regions subpanel therefore defaults its Create control to **Inherit**, not
**None**, whenever the whole is hidden.

---

## Contract B — Colour is layered and owned

### B.1 The model

`_atom_color_map` (a flat canvas-wide dict) is replaced by **ordered layers**:

- one **base layer** owned by `whole`;
- one layer per **region**, above the base.

A region's layer covers only its own atoms. Python resolves precedence and
sends only the affected atoms to the frontend; the Mol\* per-atom colour theme
(`themes/per-atom-color.ts`) stays as it is and keeps receiving a resolved map.

### B.2 Precedence — one `order`, not two (Contract O)

> **Superseded in part by Decision 2.** For atoms drawn **opaquely** by a region, precedence is
> subsumed by ownership: an atom's colour is its owner's. The rules below still govern atoms that
> no region owns, and atoms under a **translucent** region (R-O1). `order` still decides which of
> two overlapping opaque regions is the owner.

1. Any region layer beats the whole's base layer.
2. Between two overlapping region layers, **the most recently created or updated
   region wins**.

Rule (2) requires a materialised order. Today precedence would fall out of
`dict` iteration order, which `import_state` does not reproduce — reloading a
session would silently repaint the overlap zones.

**Decision B (2026-07-10): a single `Region.order`.** An earlier draft of this contract
introduced `color_order` for colour precedence and left render order unaddressed. Two counters
that both mean *"who is on top"* would inevitably desynchronise. There is **one** monotonically
increasing `order` per region, bumped on creation and on any colour or visual update, and it
governs:

- which region's colour layer wins over shared atoms;
- which region paints shared atoms, if exclusive ownership is adopted (Decision 2);
- render/draw priority between overlapping representations otherwise.

`order` is **serialised**, and `import_state` restores the **high-water mark** so that regions
created after a reload keep winning over those restored from disk. A counter that restarts at
zero silently inverts the precedence of every overlap. `view.regions` exposes `raise_to_front()`
/ `send_to_back()` so ordering is controllable, not merely incidental.

### B.3 Semantics of the reset operations

- `Region.reset_colors()` clears **that region's layer only**. What appears is
  whatever lies beneath: the whole's base layer, or a lower region's.
- `Region.set_color_by_values(..., replace=…)` is **redefined**: `replace` acts
  **within the region's layer**, never on the canvas. (Public-API semantic
  change; see §Migration.)
- `Whole.reset_colors()` clears **the base layer across the whole system**. The
  regions keep their layers, so the screen may not change where a region covers.
  The reset becomes visible under a region only once that region is hidden or
  its own layer is cleared. This is the intended, user-confirmed semantics.
- A canvas-wide wipe is an explicit, separate operation: **`view.reset_all_colors()`**.

### B.4 A region with no representation may still be coloured

A region in state **None** has no representation of its own, but its atoms are
painted by the whole. Its colour layer therefore still applies. **Colouring
without representing is a legitimate, cheap operation** and must work.

### B.5 The per-atom theme is a decorator, not a replacement

Per §0.3, an atom with no colour in any layer must render with **the theme the representation
would otherwise use** — not with a grey `DEFAULT_COLOR`.

- `msv-per-atom` takes a **base theme** parameter and delegates to it on a miss.
- `_applyPerAtomColorTheme()` stops being applied unconditionally to *all* components. A
  component gets the per-atom theme only while some layer covers atoms it draws.
- Clearing the last layer over a component **restores its configured theme**, it does not
  re-apply an empty per-atom theme.

**What lies beneath a layer — the resolution order.** Every object has *two* colour mechanisms:
a representation-level structural theme (`color_scheme`, `molstar_color_theme`, a uniform
`color`, all living in `repr_params`) and a per-atom colour layer. They are not rivals; they are
stacked. For any atom, the colour is the first of:

1. the per-atom layer of the region that **paints** that atom (the topmost visible region with
   an own visual);
2. that same region's own structural theme;
3. the `whole`'s base colour layer;
4. the `whole`'s structural theme (`element-symbol`, `msv-physicochemical`, …).

Rules 1–2 are skipped for an atom no region paints. Rule 4 is owned by `whole`
(`studio_whole_subpanel.md`), not by the System subpanel, and is serialised.

This is the answer to a question the first draft of this contract left undefined, and it is the
same class of ambiguity that produced every bug catalogued in §0.

### B.6 Layer lifecycle

| Event | Effect on layers |
|---|---|
| `region.delete()` | its layer is dropped; whatever lies beneath reappears |
| `region.rename(new_tag)` | the layer follows the tag; `color_order` is preserved |
| `region.duplicate()` | the copy receives a **copy** of the layer and a **fresh** `color_order` (so it wins over its source) |
| boolean composition | the result is a new region with **no** layer (colour is not inherited from operands) |
| `apply_system_edit` / rebuild | every layer is remapped through `atom_index_map` **and re-sent**; atoms that disappear drop out of the layer |
| transient regions (§A.5) | never own a layer |

The rebuild row is a **bug fix**, not new behaviour. `_remap_atom_color_map()`
(`viewer/core.py:1757`) already remaps today's flat map through `atom_index_map`, but it
**never re-sends it**, and `clear_all` does not clear the frontend map either
(`clearPerAtomColors` is called only from the `clear_atom_colors` handler). So after any
system edit the browser keeps the *old* index → colour map and paints the wrong atoms. The
layer model must remap **and** resend.

### B.7 Protocol

`clear_atom_colors` gains an optional `atom_indices: number[]`. Absent ⇒ clear
everything (today's behaviour, still used by `view.reset_all_colors()`).
Present ⇒ clear only those atoms. Colour writes send only affected atoms.

---

## Contract R — A region is a recipe, not a set of atoms

**Decision 1, confirmed by the maintainer (2026-07-10).**

Today a region **is** a tuple of indices, and `provenance` was designed as decorative text for
the Inspect panel. Invert it: **the recipe is primary; `atom_indices` is its cached result.**

### R.1 `Region.provenance` is executable

`Region.provenance` is a public, read-only mapping. It does not exist in any form today
(`grep -rn "_provenance" molsysviewer/` returns nothing), despite `studio_region_subpanel.md`
§5 describing it in the indicative.

| `kind` | Payload | Re-evaluable |
|---|---|---|
| `query` | `expression`, `syntax` | yes |
| `split` | `element`, `value` (e.g. chain label) | yes |
| `complement` | `of` (list of tags) | yes |
| `boolean` | `op`, `operands` (ordered list of tags) | yes, if its operands are |
| `duplicate` | `of` (tag) | yes |
| `active_selection` / `saved_selection` | indices only | **no** |
| `imported` | `state_version` | as recorded |

### R.2 `atom_indices` is derived

Since the recipe is primary, `Region.atom_indices` becomes a **read-only property**: the cached
result of the last evaluation. Assigning to it is meaningless and must be impossible. (Today it
is a plain public attribute, like `representation`, `preset`, `repr_params` and `tag` — see the
symmetry work in `scene_master_plan.md`.)

### R.3 Two modes, and two kinds of recipe

`Region.mode` ∈ {`static`, `dynamic`}.

- **`static`** — the recipe is evaluated once; the indices are frozen. Default.
- **`dynamic`** — the recipe is re-evaluated as the scene changes. This is what makes
  *"waters within 5 Å of the ligand"* expressible at all, and it is bread-and-butter for
  trajectory work.

Orthogonally, every recipe carries **`frame_dependent: bool`**:

| Recipe | `frame_dependent` | Why |
|---|---|---|
| `molecule_type == "protein"`, `chain_index == 0`, a split, an entity | `False` | topological: identical in every frame |
| anything with `within` / a distance predicate | `True` | geometric: depends on coordinates |
| a boolean/complement | `True` iff any operand is | propagates |

A `dynamic` region whose recipe is **not** `frame_dependent` costs **nothing** during playback:
its result cannot change. This distinction is what makes dynamic regions affordable.

A region born from an interactive click (`active_selection`, `saved_selection`) has **no
recipe**, only indices. It is permanently `static`, and `mode="dynamic"` on it must raise.

### R.4 Where recipes are evaluated (Decision A, 2026-07-10)

**In Python, lazily, with one consolidated message per frame.**

Evaluating in TypeScript would require porting the MolSysMT selection grammar to the frontend,
breaking the invariant that *making* atom sets goes through MolSysMT. Rejected.

The evaluation contract:

1. Evaluation is **lazy**: a `frame_dependent` dynamic region is re-evaluated only when the
   frame it needs is actually displayed.
2. Results are **cached** per `(region, structure_index)`.
3. A frame change emits **one consolidated message** carrying the atom-index deltas of *all*
   dynamic regions that changed. Never one message per region.
4. Non-`frame_dependent` regions are re-evaluated on **topology change**
   (`apply_system_edit`), not on frame change.
5. If the per-frame evaluation exceeds its budget
   (`message_toll_performance.md` §5.1), the viewer **warns and offers to freeze** the region to
   `static`. It never silently drops frames.

**Hard prerequisite.** One message per frame is viable at microseconds and absurd at three
seconds. Master-plan **Phase 0** (the `handleMessage` toll) must land before dynamic evaluation
is implemented. Phase 0 is therefore a prerequisite of Decision 1, not merely a performance
improvement.

### R.5 Recipes are closed under composition

The boolean of two dynamic regions is dynamic. The complement of a dynamic region is dynamic.
A boolean whose operands include a `static`-by-nature region is `static`.

### R.6 Referential integrity

`boolean`, `complement` and `duplicate` recipes reference their operands **by tag**, and tags can
be renamed or deleted. Undefined behaviour here would be the same class of ambiguity that
produced every bug in §0, so it is defined:

- Regions carry a stable, immutable, non-user-visible **`uid`**, assigned at creation. Recipes
  reference operands by `uid`, never by tag. Renaming an operand is therefore invisible to the
  recipe.
- **Deleting an operand** of a live recipe: the dependent region is **frozen to `static`**, its
  cached indices retained, and its provenance rewritten to
  `{kind: "boolean", …, broken: true, missing: [uid]}`. It keeps working; it stops re-evaluating.
  The GUI shows a broken-recipe badge. Deletion is never blocked, and never cascades.
- `view.regions` exposes the dependency graph (`region.dependents`, `region.dependencies`) so
  the GUI can warn before a destructive delete.
- **Cycles are impossible** by construction: a recipe may only reference regions that existed
  when it was created.

### R.7 Restoring recipes

Recipes reference other regions, so `import_state` must restore them in **topological order**
(dependencies before dependents). A state document whose graph cannot be topologically sorted is
corrupt and must raise, not partially load.

### R.4 Consequences

- **Rebuild becomes exact.** `apply_system_edit` re-evaluates recipes instead of remapping
  indices through `atom_index_map`. What `studio_region_subpanel.md` §5 calls "best-effort"
  becomes exact for every re-evaluable kind; remapping survives only as the fallback for
  regions that have no recipe.
- **Serialisation shrinks and travels.** A state file stores recipes, not tens of thousands of
  integers, and becomes portable to a comparable molecular system.
- **Contract C does not need a `v3`.** The format expresses `mode` and `provenance` from day
  one, which is the entire reason this decision is taken **before** serialisation is built.

Dynamic *evaluation* may be implemented after Contract C; the **model, API surface and
serialisation must exist now**.

---

## Contract C — A region serialises its whole state

### C.1 Provenance is first-class

See Contract R. `provenance` and `mode` are serialised, not derived.

### C.2 `export_state` version 2

A region serialises: identity (`tag`, `atom_indices`, `selection`, `syntax`),
`provenance`, visual state (`representation` — including the `"inherit"`
sentinel —, `preset`, `params`, `hidden`), its **colour layer** and its
`color_order`.

The document also gains the **whole**'s representation/preset/params/visibility, its
**structural colour theme** (§0.4 — today a frontend-only setting) and its base colour layer,
none of which are exported today.

`import_state` must also restore the **`color_order` high-water mark**, so regions created
after a reload keep winning over the ones restored from disk. A counter that restarts at zero
would silently invert the precedence of every overlap.

`version` becomes `2`. `import_state` reads v1 (identity only, regions restored
in state **None**, no colours) and v2. Transient tags matching
`_TRANSIENT_REGION_TAG` are **filtered on export**, not only in the summary.

### C.3 Round-trip is the acceptance criterion

`export_state` → new session → `import_state` must reproduce: the same regions
with the same visual state, the same visibility, the same colours **including
the winner in every overlap zone**, and the same provenance shown in Inspect.

---

## Migration & compatibility

These are semantic changes to a **published** public API. Each is deliberate:

| Change | Before | After |
|---|---|---|
| `Region.reset_colors()` | wiped the canvas | clears the region's layer |
| `Region.set_color_by_values(replace=True)` | replaced the canvas map | replaces within the region's layer |
| `Whole.reset_colors()` | wiped the canvas | clears the base layer |
| canvas-wide wipe | `Region.reset_colors()` or `Whole.reset_colors()` | `view.reset_all_colors()` (new) |
| `Region.reset_representation()` | rendered `cartoon` | removes the region's own visual |
| `set_representation(None, **params)` | rendered `cartoon` | state **None**; params ignored — use `"inherit"` |
| any `reset_colors()` | painted the system grey (`0xaaaaaa`) | restores the structural theme |
| colouring one region | greyed out every other atom | leaves the rest on its structural theme |
| whole's colour scheme | frontend-only dropdown in **System** | `whole.set_color_scheme()`, serialised |
| `export_state` | `version: 1`, identity only | `version: 2`, full state; reads v1 |

`new_view`, `extract` and `merge` switch to `set_representation("inherit")`.
Their observable behaviour is preserved (the region stays visible under a hidden
whole) and improves (it now follows later changes to the whole).

---

## How these contracts are tested

The defects above all survived a green test suite because **the tests assert the
message dict, not the rendered effect**. That is the pattern to break.

- `js/tests/unit/state-handler.test.ts` already drives a simulated Mol\* plugin
  and captures `addRepresentation` calls. Every rule in Contract A gets an
  assertion **there**: state **None** adds no representation; `reset` removes
  the child; `inherit` uses the whole's current type; changing the whole
  repaints inheriting regions.
- Contract B gets Python tests on layer resolution and precedence (including the
  overlap winner after an update), plus a protocol test for
  `clear_atom_colors {atom_indices}`.
- Contract C gets a real `export_state` → `import_state` round-trip test
  asserting the overlap winner survives.
- The Chromium + WebGL e2e (pending since Phase D) is the only check that
  `alpha`/`quality` reach `typeParams` on screen. It closes the loop.

**Rule adopted going forward:** a test whose name claims a visual outcome must
assert against the simulated plugin, not against the emitted message.

---

## Deferred (explicitly out of scope)

- Hiding a state-**None** region by subtracting its atoms from the whole's
  component.
- Per-representation parameters beyond the common set (`sizeFactor`,
  `ignoreHydrogens`, …).
- Live/per-frame re-evaluated regions.
- Sending layers to the frontend instead of a Python-resolved map (would be
  needed only if layer resolution ever becomes a rendering-time concern).
