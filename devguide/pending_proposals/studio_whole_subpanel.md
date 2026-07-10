# Proposal: Studio → Whole subpanel (the baseline structure)

**Status:** proposed (2026-07-10). **Not implemented** — the subpanel is a `RoadmapPanel`
placeholder (`ui/panels/roadmap-panel.ts`, registered in `group-panel.ts:321`).

**Scope:** the **Whole** subpanel of the **Studio** panel: complete GUI control over the
baseline molecular structure (`view.whole`) — its presence, its representation, its colour,
and its identity — without dropping to Python.

> **Normative source:** `region_contracts.md`. Whole and Regions are **not independent
> subpanels**. They are the two ends of the same three contracts: the whole owns the base
> representation that regions may inherit, and the base colour layer that region layers stack
> on top of. Neither can be finished without the other.

---

## 1. Why

### 1.1 The Whole is the only object every session has

A viewer always has a whole; regions, selections and measurements are optional. Yet the
Whole subpanel is the emptiest in Studio: a static "Feature Roadmap" card listing four
bullets. Everything a user wants to do to the baseline structure — restyle it, make it
translucent so a region shows through, colour it by B-factor, hide it to inspect a pocket —
requires Python today, or is buried in another subpanel.

### 1.2 The Python API for `whole` is **not** complete

Verified against `molsysviewer/whole.py`. Present: `set_representation`, `show`, `hide`,
`select`, `get`, `info`, `contains`, `is_composed_of`, `focus`, `set_color_by_values`,
`reset_colors`.

Missing, with evidence:

| Gap | Evidence | Consequence |
|---|---|---|
| **No public read of its own state** | `_representation`, `_preset`, `_repr_params` are private, yet read via `getattr` from **four** places: `new_view.py:120-122`, `viewer/molsysmt_interface.py:31-34`, `viewer/core.py:1848-1854` (the rebuild path) and `tools/basic/*` | the library itself must touch privates; no GUI or add-on can render the current style |
| **No public visibility read** | state lives in `view._global_hidden`; `Whole` has no `visible` / `hidden` accessor. Read via `getattr` from `tools/basic/extract.py:64` and `merge.py:122` | the panel cannot render the Show/Hide toggle from truth |
| **`set_representation` silently shows** | `whole.py:53-54` | causes Bug 1 of §1.2.1; no way to restyle a hidden whole |
| **No public read of the active scene style** | `styles._last_applied_name` is private and is cleared by `whole.set_representation()` | the panel cannot show, or protect, the named style (§1.2.2) |
| **No `reset_representation()`** | `Region` has one; `Whole` does not | no way back to the load-time style |
| **No `set_color_by_attribute()`** | `Region.set_color_by_attribute` exists; `Whole` has none | "colour the system by B-factor" — the single most requested operation — is impossible without building the value array by hand |
| **No structural colour theme** | the theme is set in JS only, from the **System** subpanel (`viewer-controller.ts:975-980`) | the whole's colour scheme is not in the API, not serialised, and silently destroyed by any per-atom colouring (`region_contracts.md` §0.3, §0.4) |
| **No `get_center()`** | `Region.get_center()` exists | asymmetric |
| **`set_color_by_values` has no `replace`** | `Whole` always replaces the canvas map (`whole.py:201-208`) | incompatible with the layer model |
| **No canvas-wide colour reset** | `Whole.reset_colors()` and `Region.reset_colors()` share one body and both wipe everything | there is no honest global operation, and no honest scoped one |

So: **no, the API is not complete.** It is, in fact, less complete than `Region`'s — the
subordinate object has capabilities its base lacks. Closing that asymmetry is the first
phase of this proposal, and several Regions phases depend on it.

### 1.2.1 It is also not *correct*: an undocumented side effect and two rebuild bugs

`Whole.set_representation()` sets `self._view._global_hidden = False` (`whole.py:53-54`).
**Changing the representation shows the whole.** The docstring mentions it in passing ("If the
global representation was hidden, this call will show it again"); nothing else in the codebase
accounts for it. Two consequences, both verified:

**Bug 1 — a hidden whole reappears after `apply_system_edit`.** In
`_rebuild_view_from_current_molsys` (`viewer/core.py`):

```python
1848:  if getattr(self.whole, "_preset", None) is not None or getattr(self.whole, "_representation", None) is not None:
1849:      self.whole.set_representation(...)      # ← resets _global_hidden to False
1856:  self._remap_atom_color_map(atom_index_map)
1858:  if self._global_hidden:                     # ← already False
1859:      self._send({"op": "hide_global", "target": "global"})
```

The re-send of the representation clears the very flag the next line tests. A whole that was
hidden **and** carried an explicit representation or preset comes back visible after any system
edit.

**Bug 2 — per-atom colours go stale on rebuild.** `_remap_atom_color_map()`
(`viewer/core.py:1757`) remaps Python's map through `atom_index_map` but **never re-sends it**,
and `clear_all` does not clear the frontend map either (`clearPerAtomColors` is called only
from the `clear_atom_colors` handler). After an edit, the browser still holds the *old*
index → colour map. Colours land on the wrong atoms.

Both are fixed as part of Phase 1 (side effect) and of the colour-layer work in
`region_contracts.md` §B.6 (rebuild remap must resend).

### 1.2.2 `view.styles` sits on top of `whole`, and the two clobber each other

`styles.apply()` delegates to `whole.set_representation()` (`styles.py:299-304`) and then
records `_last_applied_name`. In the other direction, `whole.set_representation()` calls
`self._view.styles._clear_cached_name()` (`whole.py:64-65`).

Therefore **any representation change made from the Whole subpanel silently drops the active
scene-style name.** The user applied "publication", nudges the opacity, and the scene is no
longer named — with no feedback anywhere.

The whole summary must carry `scene_style_name`, the panel must display it, and it must say
plainly that a manual change clears it. This coupling is not optional to model: `styles` is a
published surface (`devguide/styles_first_slice.md`) and the Whole subpanel is the other way
into the same state.

### 1.3 There is no JS → Python channel for the whole at all

`set_global_representation`, `show_global` and `hide_global` are **Python → JS** messages
(`viewer-controller.ts:2142-2144`). Nothing in the `PanelAction` union (`ui/panels/types.ts`)
concerns the whole. The Whole subpanel is not "under-featured": it is **unwired**.

### 1.4 One control already exists — in the wrong subpanel

The **System** subpanel's *Colour scheme* dropdown (`system-panel.ts:394-402`) calls back into
`viewer-controller.ts:975-980`, which swaps the molecular colour theme of every component
between `element-symbol` and `msv-physicochemical`. That is the whole's structural colour
theme, living in another subpanel, bypassing Python entirely.

It moves here. **System** keeps what it is good at: the interactive strips of the molecular
system (chains, groups), hover/pick/context. **Whole** owns the baseline structure's visual
identity.

---

## 2. What "complete control" means

From the GUI, a user must be able to:

1. **Presence** — show / hide the whole, and focus the camera on it.
2. **Represent** — all 12 representations, all presets, opacity (`alpha`), render quality,
   and a **reset** to the load-time style.
3. **Colour** — choose the structural colour theme (element, physicochemical, chain,
   secondary structure, …), set a uniform colour, colour by an existing structural attribute
   (B-factor, occupancy, charge), reset the whole's colour layer, and — explicitly and
   separately — reset **all** colours on the canvas.
4. **Inspect** — atom/group/chain/molecule/entity composition, geometric centre, and the
   `contains` / `is_composed_of` predicates, which today have no GUI surface anywhere.

---

## 3. The coupling with Regions (this is the point of the document)

Everything below follows from `region_contracts.md`. The Whole subpanel is where the user
feels the contracts.

### 3.1 Representation — the whole is what regions inherit

Contract A defines three region states: **None** (no own visual), **Inherit** (own visual,
using the whole's **live** type), **Own**.

- Changing the whole's representation here **repaints every region in state Inherit**. The
  panel must say so: *"3 regions inherit this representation."*
- **Hiding the whole makes every state-None region disappear**, because nothing else paints
  their atoms. The panel must warn before it happens, with the count. This is not
  hypothetical: `new_view(selection=…)` hides the whole (`new_view.py:118`), and so do
  `tools/basic/extract.py:65` and `merge.py:123`.
- Conversely, a region in state **Inherit** or **Own** survives a hidden whole. That is the
  canonical "show me only the binding site" scene.

### 3.2 Colour — the whole owns the base layer and the theme beneath it

Contract B stacks colour layers: the whole's **base layer**, then one layer per region,
newest on top.

- `whole.reset_colors()` clears the **base layer only**. Where a region layer covers, the
  screen does not change; the reset becomes visible when that region is hidden or its layer
  cleared. The panel must not pretend otherwise — it reports *"covered by 2 region layers"*.
- Beneath the base layer sits the **structural colour theme** (§1.4). The per-atom theme
  must **decorate** it, not replace it (`region_contracts.md` §B.5). Today it replaces it,
  which is why any colour write greys out every uncoloured atom.
- `view.reset_all_colors()` — the honest canvas-wide wipe — lives here, and only here, as a
  clearly-marked destructive action.

### 3.3 Scene styles — the third surface onto the same state

`view.styles` (the scene-look styles of `devguide/styles_first_slice.md`) writes the whole's
representation, and the whole's representation clears the style's name (§1.2.2). The Whole
subpanel is therefore the third writer of one piece of state, alongside `styles.apply()` and
`whole.set_representation()`.

The panel shows the active `scene_style_name` when there is one, and states that editing the
representation here clears it. It does **not** silently re-apply or invent style names.

### 3.4 Serialisation

Contract C exports the whole's representation, preset, params, visibility, **structural
colour theme** and base colour layer. None are exported today (`viewer/state.py` writes only
`annotations`, `measurements`, `selections`, `regions`). Without this, "reload the session"
cannot restore what the user was looking at.

---

## 4. Design — subpanel layout

Four blocks. See `studio_whole_subpanel_ui_design.md` for the visual spec.

### A. Presence & camera
`Show` / `Hide` toggle (`whole.show()` / `hide()`), `Focus` (`whole.focus()`). The Hide
control carries the state-None warning of §3.1.

### B. Representation
The **same style composer component as Regions**, shared, not forked: representation select
(12 real types from `view.representations`), preset select (`view.presets`, mutually
exclusive), opacity slider (`alpha`, fired on `change`/mouseup), quality dropdown, and
`Reset representation` (→ load-time style). An inline note reports how many regions inherit.

### C. Colour
Structural theme select (the migrated *Colour scheme*), uniform colour picker, `Colour by`
attribute dropdown gated to the attributes actually present in the system, `Reset colours`
(base layer), and a visually distinct `Reset all colours` (canvas-wide, destructive).

### D. Inspect
Composition (atoms, groups, chains, molecules, entities), geometric centre in the current
playback frame, and the `contains` / `is_composed_of` predicates. Fetched lazily, exactly
like the Regions `ⓘ` panel and through the same request/response idiom.

---

## 5. Architecture / How

### 5.1 Public Python API first

New on **`Whole`** (each `@signal @digest`, `_molsys` index space):

- `representation`, `preset`, `params`, `visible` — public read-only properties. `new_view`,
  `extract`, `merge`, `molsysmt_interface` **and the rebuild path in `core.py`** stop reaching
  into privates.
- `set_representation(..., keep_hidden: bool = False)` — the implicit "showing" side effect
  becomes opt-out, and the rebuild path passes `keep_hidden=True`, fixing Bug 1 (§1.2.1).
  Default stays `False` so existing behaviour is preserved for users.
- `reset_representation()` — revert to the load-time style. Note that `Whole` is
  **re-instantiated** on a scene reset (`viewer/scene.py:409`, `self.whole = Whole(self)`), so
  the baseline must be captured at load, not merely in `__init__`.
- `set_color_scheme(scheme)` / `color_scheme` property — the structural theme, owned by
  Python and serialised (§1.4).
- `set_color_by_attribute(attribute, *, element, palette, value_range)` — mirrors
  `Region.set_color_by_attribute`, writing the **base layer**.
- `set_color_by_values(..., replace=…)` — `replace` acts within the base layer.
- `reset_colors()` — clears the base layer (semantic change; `region_contracts.md` §B.3).
- `get_center(structure_indices)`.

New on **`MolSysView`**:

- `reset_all_colors()` — the explicit canvas-wide wipe.

### 5.2 Backend event handlers (`viewer/core.py`)

An entirely new action family, each routing **through** the public methods above:
`set_whole_representation`, `reset_whole_representation`, `set_whole_visibility`,
`focus_whole`, `set_whole_color_scheme`, `color_whole_by_attribute`, `reset_whole_colors`,
`reset_all_colors`, and `get_whole_details {request_id}` (lazy inspection).

Each echoes an updated **whole summary**: `{representation, preset, params, visible,
color_scheme, scene_style_name, available_attributes, inheriting_region_count,
none_state_region_count, covering_layer_count}`. The last three are what let the panel warn
honestly (§3); `scene_style_name` is what lets it show — and protect — the active scene style
(§1.2.2).

### 5.3 Protocol naming debt

The wire ops are `set_global_representation` / `show_global` / `hide_global`, from before the
Global → Whole rename. The Python API and the panels say **whole**. Renaming the wire ops is
a separate, mechanical change touching `viewer-messages.ts`, `viewer-controller.ts` and the
handler; it is **not** bundled into this work. Documented here so nobody "discovers" it again.

### 5.4 Shared components, not forks

The style composer built for Regions (`regions-panel.ts::renderStyleComposer`) is extracted
into a shared component before Whole uses it, exactly as `ManualQueryComposer` was extracted
for the query path. Two style composers that drift apart would be a repeat of the mistake
this whole effort is correcting.

---

## 6. Out of scope

- The **System** subpanel's strips, hover, pick and context menu. Only the *Colour scheme*
  dropdown migrates.
- **Layers** (`view.layers`) — its own subpanel, still a placeholder.
- Renaming the `*_global` wire ops (§5.3).
- Per-representation parameters beyond the common set.
- Subtracting a region's atoms from the whole's component so that a state-None region can be
  hidden (`region_contracts.md`, Deferred).
