# Scene contracts (normative)

**Status: IN FORCE.** Implemented and guarded by tests (2026-07-11). Every contract below is
live in the code, covered by the Python suite, and — for the parts that are only observable on
screen — by `js/tests/e2e/scene-contracts.e2e.ts`, which asserts against the Mol\* render tree
rather than against the messages we emit.

This file was promoted here from `devguide/pending_proposals/` when the 15-phase scene rework
closed. The plan that delivered it (`scene_master_plan.md`), the per-subpanel blueprints and the
phase briefs have been deleted: they were scaffolding, and they are in git history. **This
document is what survives**, because it is not a plan. It is the law the code obeys.

**If you are about to change how regions, the whole, colour, ordering or scene state behave,
read this first.** A change that contradicts a contract here is a bug, not a preference — or it
is a deliberate contract change, in which case update this file in the same commit and declare it
in §Migration.

**No external users.** Breaking changes are allowed and expected; they are declared in §Migration
with **no shims and no deprecation period**. (The one corpus still un-migrated is
`sandbox/Curso/`, deliberately carved out — see §Migration.)

**Scope:** this document has two normative parts. The first governs how a
**region** relates to the **whole**, to **colour**, and to **persisted state**.
The second governs non-structural scene objects: shapes, annotations,
measurements, and layers. Together they bind the public Python API, the
JS↔Python protocol, Studio, session state, and every future surface.

They exist because the codebase once had **two disagreeing sources of truth** about what is being
painted, and no notion of colour ownership. Both defects were invisible from Python and invisible
from the tests, which asserted emitted messages rather than rendered effects.

---

## 0. Why these contracts exist (evidence)

> **Read this section in the past tense.** Every defect below is **fixed**. It is kept because a
> contract you cannot see the reason for is a contract someone will "simplify" away. The code
> snippets are the *old* code. Do not go looking for them — go looking for the tests that now stop
> them coming back (`tests/regions/`, `tests/test_dynamic_regions.py`,
> `js/tests/e2e/scene-contracts.e2e.ts`).

Five defects, verified in code, all downstream of a missing contract.

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
per-atom colouring (§0.3).

> **Resolved (Phase 12).** All four are now false: the theme is `whole.set_color_scheme()`, it is
> serialised, `Whole` owns it, and per-atom colour is a *decorator over* it rather than a
> replacement. The System subpanel's dropdown is gone; its sequence strips now mirror the whole's
> scheme instead of owning it. This paragraph is kept because it explains **why** the contract is
> shaped the way it is.

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

**R-O1 — Ownership is by fully opaque drawing.** The whole masks a region's atoms **only if that
region draws them fully opaquely**: `alpha` absent, or `alpha == 1`, on **every** representation
the region owns (a preset generates several; one translucent surface makes the region translucent).
Anything less is translucent and owns nothing: the whole keeps painting beneath it, which is exactly
what translucency promises, and stays pickable.

Without this clause, exclusive ownership **breaks the opacity slider**. A region at `alpha = 0.3`
would reveal emptiness instead of the structure behind it, and its atoms would be simultaneously
unpickable in the region (below `pickingAlphaThreshold`) and unpickable in the whole (masked to
alpha 0) — an atom both invisible and unclickable.

**Amended 2026-07-10.** An earlier wording made ownership conditional on
`alpha >= pickingAlphaThreshold` (0.5). That is the *weakest* rule that fixes picking, and it breaks
the opacity slider across the whole range (0.5, 1): a region at `alpha = 0.6` would own its atoms,
the whole would be masked beneath it, and the user would see 0.6 over the **background** instead of
over the structure they asked to see through to. Full opacity is the correct threshold: it satisfies
the visual meaning of `alpha` *and* picking safety at once, and it does not couple a scene-graph
invariant to a renderer parameter someone might change.

Blending between a translucent surface and what lies behind it is not z-fighting. It is what the
user asked for.

**R-O2 — The mask is updated by deltas**, never recomputed in full. Contract R's `dynamic` regions
re-evaluate their atom set per frame; a full mask recompute costs 26 ms at 50% ownership and the
frame budget is 16 ms. (The measurement, and the harness that produced it, live in
`js/tests/perf/` — run `npm run test:perf`; see `engineering_rules.md` §Performance.)

This is where the cost actually is. In the Phase 1 benchmark at n = 95,000, `buildSelectionMs` was
13–23 ms of a 14–32 ms toggle: **constructing the selection dominates**, and a delta makes it small.

Mol\* can express it. `mol-theme/transparency.ts` defines
`Transparency = { kind, layers: ReadonlyArray<{ loci, value }> }` — **ordered layers with values**.
A delta is a layer of `value: 1` over newly-owned atoms plus a layer of `value: 0` over released
ones. Layers accumulate, so compact them every N operations. Check whether
`mol-plugin-state/helpers/structure-transparency.ts` **appends** or **replaces** layers: if it
replaces, R-O2 needs a new helper, and a "delta state, consolidated application" fallback must be
documented as such and **not** claimed as R-O2.

**R-O3 — The ownership mask composes with the user's mask, and with the focus fade.** There are
**three** writers to the same transparency channel, not two:

| writer | `state-handlers.ts` | value |
|---|---|---|
| `updateVisibility` (user's `show`/`hide`/`isolate`, Python's `atom_mask`) | `:327` | `1` |
| `setFocusFade` (the soft spotlight of `styles.focus()`) | `:378` | `min(1, fade)` |
| ownership mask *(new)* | — | `1` |

Each currently calls `clearStructureTransparency` before writing (`:280`, `:340`), so **today the
first two already destroy each other**: applying a partial visibility wipes the focus fade, and
vice versa. That is a latent bug nobody has reported.

Composition is over **values**, not over sets — the fade is a number, not a boolean. Exactly one
method owns every transparency node. `currentVisibleIndices` remains the user's authority; ownership
never mutates it. The final transparency is a derived composition, never a replacement of the
visibility channel.

Per component:

- **region components** — the user's mask only;
- **the whole's component** — `userHiddenAtoms ∪ ownedOpaqueAtoms`, composed with the focus fade;
- state-**None** regions, and translucent regions of any state, own nothing.

**Region-vs-region ownership is out of scope until `order` exists (Phase 4).** The whole's mask is a
**union**, so which of two overlapping opaque regions is the owner does not change it. Phase 2 needs
a set and its deltas — no `ownerByAtom`, no owner stacks. Overlapping opaque regions keep z-fighting
with each other until `order` lands.

**R-O4 — `pickingAlphaThreshold` is not lowered to 0** by the viewer. At 0, a masked whole becomes
pickable again and ownership silently breaks.

### Clause replacements (now in force)

The clauses written in Contracts A and B below describe the *previous* model. Where this table
disagrees with them, **this table wins**. Read it before implementing §A or §B.

| Clause | Previous model | **In force under exclusive ownership** |
|---|---|---|
| §A.2 rule 2 (state **None**) | region has a component but no representation child; the whole paints its atoms | unchanged |
| §A.3 (`hide()` on state-**None**) | no-op that warns | unchanged — a region that owns nothing has nothing to hide |
| §A.4 (`show_only`) | delegates to `view.isolate`, reshapes the whole | hide every other region, and mask the whole **entirely**. No `isolate` call. *(A region cannot "own" atoms outside its own set; an earlier wording said so and was wrong.)* |
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
(`whole.set_color_scheme()`), not by the System subpanel, and is serialised.

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

`Region.provenance` is a public, read-only mapping. **Implemented (Phase 5).**

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
result of the last evaluation. Assigning to it is meaningless and must be impossible.
**Implemented (Phase 7).**

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
   (25 ms; `viewer/core.py:_dynamic_region_evaluation_budget_ms`), the viewer **warns and
   freezes** the region to `static` and reports it through SMonitor. It never silently drops
   frames.

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
  indices through `atom_index_map`. Rebuild becomes **exact** for every re-evaluable kind;
  remapping survives only as the fallback for regions that have no recipe.
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

### Corpus status

`docs/` and `bloques.md` were migrated (2026-07-11). **`sandbox/Curso/` was deliberately left
un-migrated** — it is the maintainer's working area. Its notebooks still call `view.new_region()`,
which no longer exists, and still describe the pre-rework colour semantics. Migrating it is a
standing task, not an oversight.

Note that `docs/` notebooks are **not executed by the Sphinx build** (`docs/conf.py` sets
`nb_execution_mode = "off"`), so a green `make html` proves nothing about whether the code in them
runs. The only real check is `python docs/execute_notebooks.py`.

---

## Known Mol\* behaviour that the contracts do not control

**Mol\* silently substitutes a representation it cannot build.** Ask for a `cartoon` on a component
with no renderable polymer backbone — a one-residue chain, a ligand region — and Mol\* does not
fail: it renders **`ball-and-stick` with default params**, discarding the `alpha` and `quality`
you asked for.

So a region's *rendered* type is not proof of the type that was *requested*, and Contract A's
"Own" state can be Own-in-Python and something-else-on-screen. Nothing in this document prevents
it, and no test will catch it for you. If a user reports "I asked for cartoon and got sticks",
this is why.

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

---

# Part II — Scene-object contracts: shapes, annotations, measurements, layers

**Status: IN FORCE.** Implemented and guarded by Python, JavaScript, and real
browser tests (2026-07-14). This part was promoted from
`devguide/pending_proposals/` when the nine-phase scene-object rework closed.

**Scope.** The four Studio subpanels that the original scene rework did not touch:
**Measures**, **Annotations**, **Shapes** and **Layers** — and the Python
domains behind them (`view.measurements`, `view.annotations`, `view.shapes`,
`view.layers`).

The first scene rework (15 phases, closed 2026-07-11) fixed the *structural*
half of the scene: the whole and the regions. The scene-object rework closed
the non-structural half on 2026-07-14. This part preserves the audit evidence
and the contracts the implementation now satisfies.

> **The contracts in Part I remain in force.** Nothing here weakens Contract
> A, B, R, C, or H.

---

## 0. Why this document exists (evidence)

> **Read this section in the past tense.** Every defect below is fixed. The
> evidence remains so future changes do not accidentally recreate the same
> split sources of truth.

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
[`session_reproducibility.md`](session_reproducibility.md) exists to
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

### 0.11 Sections serialise as live scene objects

Resolved after the scene block: state v2 carries each clipping plane's tag, point,
normal and invert flag. `import_state` reconstructs a live `Section` through
`scene.add_section`, and `scene.sections()` exposes the restored handles for further
editing. The round-trip is checked both in Python and against Mol*'s real
`clipObjects` state in Chrome.

### 0.12 Add-on shapes are ordinary shapes — and the panel will let the user delete them

Add-ons do not have a private channel. They create shapes by **calling the public
API** — the live example is ElastNetMT:

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
  model today, so a shape from ElastNetMT is indistinguishable from one the user made.
  Adding `owner` to the record (and showing `· from elastnetmt` on the row) is cheap,
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
existing contracts in [`scene_contracts.md`](scene_contracts.md) (A, B, R, C, H)
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

#### A summary is runtime-only — **so the canonical `ready` projection must cover it**

This is the corollary that is easiest to miss and most expensive to miss.

Because a summary is sent with `_send_runtime_only`, it is an immediate
projection of state, not stored command history. A frontend that attaches later
therefore receives it from the embedded-runtime canonical snapshot:

```python
elif event == "ready":
    self._ready = True
    messages = self._build_embedded_runtime_snapshot(...)
    for message in messages:
        self._deliver_transport_message(message)
```

**Every summary op that Python can publish must be present in the canonical
panel/embedded projection.** Forget it and the panel renders **empty** while the
canvas happily shows the objects whenever the frontend attaches fresh. Coverage
is derived from the registered `_sync_<domain>_runtime` surface and asserted by
result; the contract no longer requires a parallel list of explicit calls in
the `ready` handler.

There must be a test that opens a fresh frontend and asserts the panel is populated.

Two more rules that the region implementation earned the hard way:

- Use **`_send_runtime_only`** for live updates: a summary is a projection of
  state, not a command. Late attachment is owned by the canonical projector.
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
[`post_1.0/annotations_mvs_machinery.md`](pending_proposals/post_1.0/annotations_mvs_machinery.md).
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
- Clipping planes get a **`sections`** key and restore as live `Section` handles,
  not as message-only records.

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
- **`broken` is a state, not a tombstone: the object can be repaired.** Repair is
  **explicit** — `set_anchor()` re-points the object at atoms that exist, and it becomes
  valid again. **It is not undo.** `apply_system_edit` deliberately *invalidates* the
  history (verified: the undo stack is emptied), so a structural edit cannot be walked
  back — which is precisely why the object must survive the edit rather than be deleted
  by it. A deleted object cannot be repaired by anything.
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
  to the Viewport panel's world, not to these four. Their panel remains out of scope,
  but their state persistence is resolved in §0.11: clipping planes survive a
  save/reload as live `Section` handles.
- **An `owner` field on scene objects** (so the panel can say `· from elastnetmt`).
  Cheap and useful, but it is new API surface and this block has enough (§0.12).
  Deferred on purpose.

### Contract S8 — A scene message never overtakes the structure it describes

**Established 2026-07-31, after the defect below shipped and was found by hand.**

Every handler that draws into the scene needs a `Structure` to draw on, and each
one gives up silently when there is none — `addMeasurement` opens with
`if (!structure) return;`, and the annotation and region handlers do the same. So
the ordering guarantee is not a nicety: it is the only thing standing between a
correct scene and a silently empty one.

On the JSON path that guarantee was free. `index.ts` serialises inbound messages
through a promise chain that **awaits** `handleMessage(load_molsys_payload)` before
taking the next one, so nothing could arrive early. **The array-native data plane
removed it without replacing it.** `_try_send_array_native_molsys` returns as soon
as `structure_data_begin` is on the wire; the structure is built in the browser
several ack round-trips later, when the last chunk lands and
`array-native-stream.ts` awaits `onComplete` before notifying
`structure_data_complete`. Everything Python sent in between reached a frontend
with nothing to draw on.

The damage was real and invisible in equal measure:

```python
v = demo["181L"]                    # queued in _message_history
v.measurements.add_distance(...)    # queued too
v                                   # displayed -> frontend says "ready"
```

On `ready` the whole history was replayed in one synchronous loop: the stream
started, and the measurement went out **immediately behind `structure_data_begin`,
before a single byte of coordinates**. The measurement existed, was correct,
stored and queryable through the API — and was never drawn. No exception, no
warning, a green suite. It survived two rounds of smoke testing looking like a
Mol\* problem, because a measurement made from the Studio subpanel *did* render:
that one is created interactively, long after the structure exists.

`_answer_popup_scene_snapshot` was the second instance of the same defect: it
streams the generation to the popup endpoint and then sent the entire projected
scene at once, so a popped-out canvas showed the molecule and nothing else.

**The rule.** `_send_widget_message` holds scene messages while a structure
generation is in flight and flushes them, in order, once the frontend confirms the
structure is applied (`structure_data_complete`, the JSON fallback, or a cancel).

**The escape hatch is a different method, not a list of exempt op names.**
Transport, bootstrap and blocking request/response traffic call
`_transmit_widget_message` directly:

- the data plane itself (`structure_data_begin` / `_chunk` / `_cancel`) — holding
  it would deadlock the very completion the queue is waiting for;
- `widget_runtime_source` / `popup_source` — the frontend is blocked on these to
  exist at all, and cannot ack a stream until it does;
- `request_camera_snapshot` / `request_image_export` — they busy-wait on the
  kernel thread for an answer that deferral would prevent arriving.

An allowlist of op names would have been the same defect in a new place: a list
that must agree with reality, with nothing forcing it to (§0, and the digester and
Qt-manifest drifts). A method boundary cannot silently fall out of date.

**Order within the flush is part of the scene**, not an implementation detail:
regions layer by arrival and colours resolve after their components, so the queue
must be drained FIFO. If a newer generation starts mid-flush, the remainder waits
for *it* rather than overtaking the structure it is about to replace.

**Consequence for any future asynchronous delivery.** Anything that makes a
message's *application* later than its *transmission* re-opens this hole. The
receiver-side barrier (the frontend holding scene ops until its own structure is
ready) is the more general answer and is filed as a post-1.0 proposal; until then,
S8 is enforced on the Python side, where the timeout and fallback machinery that
makes it safe already lives.

Tested in `tests/test_structure_stream_ordering.py`, including the fallback path
(the backlog must not be stranded, nor precede the JSON load) and the JSON-only
frontend (no stream, so nothing is ever held).

### Contract S9 — A half-built scene must never be treated as the finished one

**Established 2026-08-01, from a defect found by hand. Status: implemented and
measured (`75069724`, `34da6066`, `d0e6013c`). Delivery of the mandatory
diagnostic signal is tracked separately as active defect Z2 in
`pending_proposals/open_items_after_the_2026_08_smoke_round.md`.**

Camera authority is target-specific. In a live widget or popup, camera remains
ephemeral endpoint-local state and is not part of Python's popup snapshot. A
static HTML export is the deliberate exception: Python requests and captures the
current camera while the host still exists, then embeds it after the canonical
scene projection because the exported artifact has no host to query later.

Mol\* derives state from the scene *as it currently stands*, and some of what it
derives is **not recoverable** once the scene is complete again. Any moment in
which our scene is transiently empty or half-built is therefore not a cosmetic
flicker — it is a window in which Mol\* records conclusions we cannot undo.

#### The instance that taught us

`whole.set_representation("cartoon")` opened the view *inside* the molecule, with
the wheel unable to zoom back out; only "Reset view" recovered it. The chain,
measured in a real browser rather than reasoned about:

1. `setWholeRepresentation` **removes** the old global representations and *then*
   builds the new ones. `commit()` returns long before the geometry arrives.
2. While the scene is empty, `commitScene` re-derives the camera bound from a null
   bounding sphere: `camera.state.radiusMax` collapses from 30.5 to **0.01**
   (`canvas3d.js:744`).
3. The trackball's `checkDistances()` runs on **every frame**, not only on input,
   and clamps the camera to `radiusMax * 1000` (`controls/trackball.js:404`). The
   bound becomes 10 where 181L needs ~80. Measured directly: with `radiusMax`
   forced to 0.01 and the scene left untouched, the camera moved from 79.79 to
   exactly 10 within five frames.
4. `radiusMax` recovers with the geometry. **The camera does not** — the clamp
   wrote `camera.position`.

#### The condition that hid it

The empty window only opens when the mutation lands while the viewer is *still
settling from the load*:

| swap issued | scene empty | lowest `radiusMax` |
|---|---|---|
| +300 ms after load (viewer still settling) | 20–1020 ms, varies per run | **0.01** |
| +0 ms | ~100 ms | 10 |
| +1500 ms (settled viewer) | never | 30.5 |

Which is exactly why nobody caught it: changing a representation by hand on a
quiet viewer is clean. Contract S8 then made the burst-after-load the *normal*
case, because the whole scene now replays immediately behind the structure. **S8
did not create this defect; it made a pre-existing one reachable.** Two correct
changes can combine into a broken one, and only the combination is observable.

It also survived three rounds of automated probing: the headless harness draws
about **one frame** when idle, and the clamp needs frames. A defect that needs a
continuously drawing canvas is invisible to every test we have.

#### There are two damage vectors, not one

The chain above is the one that was measured, but reading `canvas3d.js` afterwards
turned up a **second, independent** way the same harm happens, with a *different*
trigger. `checkDistances()` takes the smaller of two bounds:

```js
const maxDistance = Math.min(Math.max(camera.state.radiusMax * 1000, 0.01), p.maxDistance);
```

- **`camera.state.radiusMax`** — re-derived on every commit from
  `scene.boundingSphere` (`canvas3d.js:744`). Trigger: the scene is **empty**.
- **`p.maxDistance`** — the trackball's own bound, set by `resolveCameraReset`
  from `scene.boundingSphereVisible` as
  `max(maxDistanceFactor * radius, maxDistanceMin)` = `max(10 * radius, 20)`
  (`canvas3d.js:678-685`). Trigger: nothing is **visible**.

The second is nastier in two ways. It keys on *visibility*, not existence — so
hiding the whole while its regions have not drawn yet can pin it without the scene
ever being empty. And it is not guarded by `radius > 0`: the `camera.setState`
below it is, but `controls.setProps({ minDistance, maxDistance })` runs
regardless. A scene that commits with nothing visible leaves `p.maxDistance` at
**20** — which then clamps the camera *even with a perfectly healthy
`radiusMax`*.

**Consequence for the guard.** `manualReset` covers both vectors through the same
door, because `resolveCameraReset` returns early unless `cameraResetRequested`,
which `commitScene` only sets when `!p.camera.manualReset`. But there are two
other ways that flag gets set, and **neither is gated by `manualReset`**:
`syncVisibility()` (only when `radiusMax === 0` exactly, which the guard prevents)
and `requestCameraReset()` — which is a *public API we call*: `resetView()` →
`PluginCommands.Camera.Reset`.

So a "Reset view" that lands while a mutation is in flight pins `p.maxDistance` to
20 and strands the user — the very action they reach for to escape. Not
hypothetical now that S8 replays a burst: `reset_view` can sit in the message
history like anything else.

#### The rule

**One principle: never let Mol\* draw conclusions from a scene that is not
finished.** Two mechanisms, chosen by which case you are in — they are not
alternatives, and neither one covers the other's case.

**A. When the mutation has a successor, keep the predecessor until it is ready.**

A representation change is a *parameter* change, not a demolition: `type` lives in
the same params bag as `colorTheme` on the `StructureRepresentation3D` transform,
which is why `applyStructuralColorInPlace` never flickers. Updating the node in
place keeps the old geometry on screen until the new is ready — measured at **0 ms
empty in every condition tested**, against 20–1020 ms for remove-then-add.

This works whenever the *shape of the state tree* is unchanged: same set of nodes,
different params. It does not when the node set itself changes — a preset produces
one component-plus-representation per category, and "one node becomes three"
cannot be expressed as a param edit. **Those paths add before they remove**, which
is the same principle one level up, not a lesser fallback.

There is no memory argument for preferring one over the other: both hold the old
geometry until the new exists, because that is what "no gap" *means*. The only
difference is whether Mol\* manages the overlap (in-place) or we do
(add-before-remove). Prefer in-place where it applies, for the smaller surface.

**B. Camera bounds are ours, not derived from whatever the scene happens to be.**

Some mutations have no successor to hold onto: `clear_scene`, replacing the
structure, `clearGlobalRepresentations()` on the load path. Mechanism A cannot
help; the scene *will* be empty.

The tempting answer is a per-mutation guard — hold `camera.manualReset` while the
mutation runs. **It is the wrong shape, for the third time on this defect.** It
needs a definition of "the mutation has finished" that nothing supplies; it must
be threaded through every current and future scene-emptying path; and it does not
close the `requestCameraReset` hole, because that sets `cameraResetRequested`
directly. A guard that must be remembered at every call site is the drift pattern
(§0) with extra steps.

**Take the authority instead, once, and never negotiate over a window again:**

```ts
canvas3d.setProps({
    camera: { manualReset: true },
    trackball: { autoAdjustMinMaxDistance: { name: "off", params: {} } },
});
```

- `manualReset: true` — `commitScene` never touches `radiusMax`
  (`canvas3d.js:744` is gated on it). The collapse is not *avoided*, it is
  **impossible by construction**, whatever the timing.
- `autoAdjustMinMaxDistance: off` — `p.maxDistance` keeps its `1e150` default
  instead of `max(10 * visibleRadius, 20)`. The visibility vector disappears, and
  `resolveCameraReset` becomes a no-op on an empty scene (its `setProps` is
  skipped, its `camera.setState` is already behind `radius > 0`), which **closes
  the `requestCameraReset` hole without having to order camera ops at all**.

Framing then costs one explicit `requestCameraReset()` once the load has content —
and it is not extra bookkeeping, because that call sets `radiusMax` from a
*finished* scene on its way past (`canvas3d.js:691`, not gated by `manualReset`).

Measured, default configuration versus this one, swapping on an unsettled viewer:

| | trackball bound | `radiusMax` through the swap | distance after load |
|---|---:|---:|---:|
| default | 305 (= 10 × radius) | can collapse to 0.01 | 79.79 |
| authority taken | **1e150** | **30.534, immovable** | 79.79 |

**What this gives up, stated plainly.** Mol\* also re-frames opportunistically when
geometry appears outside the current view (`shouldResetCamera`). We lose that. It
is arguably the *source* of surprise camera moves rather than a feature, but it is
a behaviour change and must be judged as one, not waved through. `minDistance`
also reverts from `5` to `0.01`, letting the user zoom inside atoms; set it
explicitly on the trackball props if that matters.

One real obligation follows, and it is sharper than it looks: `resolveCameraReset`
clears `cameraResetRequested` whether or not it did anything, so a reset requested
against an empty scene is *consumed and lost*. Request it when the scene has
content, and re-request if `radiusMax` is still 0 afterwards — Mol\*'s own
`syncVisibility` uses exactly that test. A bounded retry, not a transaction.

It is sharper because **`manualReset` also removes Mol\*'s own safety net**. Its
auto-reset is what quietly rescued the camera in the harness, and it is why the
first regression test passed with the fix removed. Once authority is taken, the
explicit request is the *only* thing that frames the scene. Losing it has no
fallback.

#### Both levers are hidden parameters

`camera.manualReset` and `trackball.autoAdjustMinMaxDistance` are both declared
`isHidden: true`. They are typed in the `.d.ts`, so a Mol\* release that *removes*
either breaks the build loudly. A release that changes their *semantics* — say,
`manualReset` stops gating the `radiusMax` derivation — removes our protection
**silently, with everything still compiling and every test still green**.

That is what makes the detection signal (`CATALOG` + `CODES`) mandatory rather
than defence in depth: a camera left inside the scene bounding sphere after a
mutation is never a framing anyone chose, and it is the only thing that would
distinguish "still works" from "stopped working at some upgrade". Detection, never
repair — the camera is not moved behind the user; see above for why.

#### This is arguably Mol\*'s defect, and worth reporting

`checkDistances()` irreversibly relocates `camera.position` from a bound that is,
at that instant, transient and meaningless. The root is one layer below:
`getSceneRadius()` returns 0 for an empty scene, and everything downstream behaves
as though the universe collapsed to a point.

**An empty scene is not a scene of radius zero.** It is a scene about which
nothing can be concluded. Treating "unknown" as "zero" is the underlying error,
and it is not ours. Our configuration is the workaround we need now; an upstream
report is what eventually makes it unnecessary rather than permanent.

**Do not "repair" the camera afterwards.** That was the first fix attempted and it
is the wrong shape: it cannot tell a clamp from Mol\*'s own legitimate re-framing
without guessing, so it either under-fires or fights the user. Prevention has a
crisp condition; repair only has heuristics.

#### The open question in layer 2

Handing camera authority back needs a definition of "the mutation has finished",
and the obvious one does not work: while `manualReset` is true the observable that
would tell us (`boundingSphere`) is itself not what it will be. Any implementation
must answer this explicitly — a bounded wait on `reprCount` plus a deadline, and on
exit compute the bound once from the finished scene
(`camera.setState({ radiusMax: boundingSphere.radius * props.sceneRadiusFactor })`)
rather than hoping a later commit will do it.

#### Testing it

The condition that reveals the defect is *the unsettled viewer*, so a test that
swaps on a quiet one proves nothing. A test must also not congratulate itself for
Mol\*'s own recovery: in the harness, emptying the scene makes `commitScene`
request a camera reset that re-frames the structure, so the naive assertion passes
with the fix removed. Assert on `radiusMax` during the window, not on where the
camera ended up.

---

### Contract S10 — The whole carries one representation, and changing it is a succession

**Established 2026-08-06, from an audit of a design record that said the
opposite. Status: in force, and pinned in `tests/e2e/scene-contracts.e2e.ts`.**

`whole.set_representation()` leaves the whole with **one** global representation.
Applying a second replaces the first; representations never accumulate at the
whole level. Regions are where several coexist, deliberately, and the layered
colour stack is where a single representation carries several colourings.

The Python model cannot express anything else — `Whole._representation` and
`Whole._preset` are single-valued — and the runtime reaches the same end by two
mechanisms, chosen by the state it starts from:

- **one representation in place**: the existing node is edited
  (`applyWholeRepresentationInPlace`), which is Contract S9 mechanism A — no
  demolition when a parameter edit will do;
- **more than one**, which is what a loader preset can leave behind: the
  successor is built first and the predecessors it did not reuse are removed
  after. Same no-gap ordering as S9, one level up.

**Why this is a contract and not an implementation note.** For months
`areas_of_opportunity_analysis.md` §2 recorded the default as deliberately
*additive*, and nothing in the suite could say which of the two was true. A
reading of that document nearly produced a false defect report to Mol\*. A rule
that no test can settle is a rumour, whichever document holds it.

**What is pinned, and what is not.** The e2e scenario asserts the surviving
representation from Mol\*'s own cells — not from `globalReprs`, which is cleared
on every change and would report succession even when nothing was removed. It
exercises the in-place mechanism, since a fixture of twelve atoms yields one
representation from every preset tried and the multi-representation state was not
reachable. The removal branch is therefore **read but not pinned**; covering it
needs a fixture whose preset genuinely splits, and that is the next step for
anyone touching this code.

## 4. How these contracts are tested

Same standard as the rework — a claim in a test name must be asserted, and every
mechanism must be verified by **mutation** (revert the mechanism, the test must
fail):

- **Python**: the summary records (content, not `isinstance(dict)`); the
  summary re-syncs after *indirect* mutations; the round-trip of `hidden`,
  `layer_tag` and the shapes; undo across each scene-object operation; an old
  (shape-less) document imports cleanly.
- **JS unit**: each new panel renders its summary, and each affordance
  dispatches the expected `panel_action` (never a direct `handleMessage`).
- **E2E, real browser** (`js/tests/e2e/`): annotations, measurements, shapes,
  and layers each have coverage proving both halves of visibility: the object
  disappears from the Mol\* render tree and the authoritative Python
  `info(tag)["visible"]` state becomes false. These are the tests that would
  have caught §0.2; no unit test can establish both halves.

A mechanical acceptance criterion, in the spirit of the Phase 12 brief:

```bash
# no panel may mutate runtime state directly
grep -n "handleMessage" molsysviewer/js/src/managers/viewer-controller.ts | grep -i "hide_layer\|show_layer"
# -> must not appear inside refreshAddonsPanel
```
