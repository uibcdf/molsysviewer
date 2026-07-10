# Proposal: Studio → Regions subpanel (native region management)

**Status:** **partially implemented** (structure landed 2026-07-09; a 2026-07-10 audit found
it rests on three broken contracts and that the GUI does not reach parity with the Python
API). See **`region_contracts.md`** (normative) and the reworked
`studio_region_subpanel_implementation_plan.md`.

> **Read `region_contracts.md` first.** It governs how a region relates to the whole, to
> colour, and to persisted state, and it **wins over this document** wherever they disagree.
> Sections below that describe capabilities not yet in the code are marked **(proposed)**.

**Scope:** the **Regions** subpanel of the **Studio** panel in MolSysViewer. Gives the
user adequate and complete control over the viewer's *native* region management —
creating, representing, composing, isolating, inspecting and managing regions —
**without having to drop to the Python API**. It is the sibling of the already
implemented Selection subpanel (`studio_selection_subpanel.md`) and reuses its
philosophy, its query composer, and its collision/undo idioms wherever they apply.

This document now records the implemented architecture. It consolidates three inputs:
the maintainer's initial analysis, a
collaborator draft (a three-section Regions Manager), and the decisions reached after
reviewing that draft. What was adopted / changed / added is recorded in §10.

---

## 1. Why

### 1.1 The model exists; the UI underuses it

MolSysViewer already models a **region** as a first-class scene object
(`molsysviewer/regions.py`, `molsysviewer/viewer/regions.py`): a **fixed atom set +
representation/preset + visibility + color + name (tag)**, materialised as a Mol\*
component. It sits at the end of the selection progression:

> explore interactively → obtain an active selection → persist it as a named selection
> → **promote it to a region** (a represented, persistent scene object).

Where a *selection* is transient/named material with **no** visual identity, a
*region* is the visual, persistent object the user actually manipulates in the scene.

The Python surface backing regions is rich and already implemented (verified in code):

- **Create:** `view.new_region(selection|atom_indices, *, tag, representation,
  complement_of_regions, syntax, **repr_params)`,
  `view.new_region_from_active_selection(*, tag, representation, **repr_params)`,
  `view.make_regions_by(element, selection, *, representation)` (one region per
  `chain | molecule | entity`), `region.new_complementary_region(tag=…)`
  (default tag `Global-<tag>`).
- **Compose (boolean):** `region.union(other) / intersection(other) /
  difference(other)`, also `|`, `&`, `-`; each accepts `tag=`, `representation=`.
- **Represent:** `region.set_representation(representation | preset, *, color, **params)`
  where `params` accepts the verified common keys **`alpha`** (opacity `[0,1]`),
  **`quality`** (`auto|lowest|lower|low|medium|high|higher|highest|custom`),
  **`color_scheme`**, `size_scheme`, `molstar_color_theme`, `molstar_size_theme`, plus
  representation-specific keys. Allowed representations (12): `cartoon, backbone,
  ball-and-stick, carbohydrate, ellipsoid, gaussian-surface, gaussian-volume, line,
  molecular-surface, point, putty, spacefill`. Allowed presets (6): `auto,
  atomic-detail, polymer-and-ligand, polymer-cartoon, coarse-surface, empty` (+ user
  presets, via `view.presets`; `view.representations` lists the types).
- **Visibility & camera:** `region.show() / hide() / show_only()` (isolate),
  `region.focus(...)`.
- **Lifecycle:** `region.rename(new_tag)`, `region.delete()`.
- **Inspect:** `region.info(...)` (a `RegionInfo` with a *molsys* section + a *region*
  section: tag, atom count, visibility, representation, preset),
  `region.get_center(structure_indices)` (centroid as a `puw` quantity in nm),
  `region.contains(...)`, `region.is_composed_of(...)`.
- **Color (scalar):** `region.set_color_by_values(values, element, palette,
  value_range, replace)`, `region.reset_colors()`. **Both are canvas-wide, not
  region-scoped** — `Region.reset_colors()` and `Whole.reset_colors()` have identical bodies
  (`self._view._atom_color_map.clear()`), and `replace=True` replaces the entire canvas map.
  Colour has no owner today. Repaired in Phase 2; see `region_contracts.md` §B.
- **Registry:** `view.regions` (dict-like `RegionsManager`) with `.info(tag?)`; overlap
  detection (`_overlapping_visual_region_tags`, `_warn_region_visual_overlap`) that
  today only emits a Python `UserWarning`.

Before this implementation, the subpanel (`renderRegionsSection`, `group-panel.ts`)
exposed only a
sliver: a flat list (tag · atom count · hidden), click-to-focus, delete,
visibility toggle, and an expandable *style composer* limited to **5 hardcoded
representations** and **4 color schemes**, with **no opacity, no presets, no
creation, no isolate, no rename, no composition, no inspection**. That is why it reads
as "empty". The gap between the model and the UI is the opportunity.

The subpanel as shipped closes much of that gap through the public Python API: three
creation origins, batch visibility, lifecycle cards, the representation/preset surface in
the style composer, ordered boolean composition, overlap assistance, and lazy frame-aware
inspection. Runtime summaries expose style capabilities and current parameters without
entering reproducible scene history.

> **Audit, 2026-07-10.** The gap is **not** closed. The Create control still offers 7
> hardcoded representations and no presets — the very flaw described above. The GUI ignores
> backend parameters that already work (`palette`, `value_range`, `element`, `new_tag` on
> complement and duplicate, `selection` on split). Multi-operand composition and provenance
> were documented but never built. And three contracts are broken beneath all of it (§6.3,
> `region_contracts.md`). The reworked implementation plan closes both the contracts and the
> parity.

### 1.2 What "complete control" means

Native region management should let a user, from the GUI:

1. **Create** regions — from the active selection, from a MolSysMT/Indices query, by
   splitting a hierarchy level (a region per chain/molecule/entity), or as a
   complement.
2. **Represent** them faithfully — all 12 representations, presets, **opacity**,
   **render quality**, color scheme / uniform color, and (new, §8) color by an
   existing structural attribute.
3. **Compose** them — union / intersection / difference between existing regions.
4. **Manage lifecycle** — rename, delete, show/hide, **isolate**, focus, and global
   show-all / hide-all.
5. **Inspect** — atom/element composition, geometric center, and be **warned about
   overlaps** (z-fighting) with a non-destructive path to resolve them.

Today only a fraction of (2) and part of (4) are covered. This proposal completes
(1)–(5).

### 1.3 Foundations: two bases, the region surfaces, shared philosophy

Regions rest on the same **two base sources** as selections (`studio_selection_subpanel.md`
§1.3):

- **Managing** regions → the **molsysviewer public API** (`view.new_region`,
  `view.regions`, `region.*`): the authority over region state and lifecycle.
- **Making** the atom set → the **MolSysMT selection API** (`msm.select`: expression →
  indices), with the region-specific addition of **boolean composition between regions**
  (`union/intersection/difference`) as a second way to produce atom sets.

On top of those, regions are reachable from several **surfaces** that share one
philosophy and never constrain one another:

1. the **molsysviewer public API** (also the managing base);
2. the **Studio → Regions subpanel** (GUI) — *this proposal*;
3. the **`molsysviewer_molsysmt` add-on** (GUI + API) — postponed;
4. the **Selection subpanel's `→ Region` promote bridge** and the **canvas right-click
   context menu** (`create_region_from_selection`), which already exist.

**Shared philosophy — invariants every surface honours:**

- a single shared region registry (`view.regions`);
- *making* atom sets goes through the MolSysMT grammar (one language) or region boolean
  composition;
- *managing* goes through the molsysviewer public API (authority for the registry and
  representations);
- one common **boolean vocabulary** (Union / Intersection / Difference) that means the
  same everywhere and matches the selection subpanel's set-operation naming;
- **no persistent operation "mode"** — the operation is chosen at the moment of acting;
- overlap between visible represented regions is **surfaced, not silently produced**.

---

## 2. What (scope)

**In scope (this subpanel):**

- **Create** regions from: the active selection, a query (MolSysMT/Indices, reusing the
  Selection subpanel's composer), a hierarchy split (`make_regions_by`), and a
  complement.
- **Represent** regions with the full representation/preset vocabulary, **opacity**,
  **quality**, color scheme / uniform color, and **color-by-attribute** (§8).
- **Compose** regions with Union / Intersection / Difference.
- **Manage** lifecycle: rename, delete, show/hide, **isolate** (`show_only`), focus,
  global show-all / hide-all, and **reset representation** (§8).
- **Inspect**: per-region composition + geometric center; **overlap warning** badge
  with a non-destructive resolve path.

**Out of scope (placed elsewhere, by decision):**

- **Geometry overlays** — `show_orientation_axes` / `show_best_fit_plane`. They are
  auxiliary 3D guides, not chemical/biological subsets, so their creation UI belongs to
  the **Overlays** subpanel. Note (§6.4): they *do* register as `Region` objects
  internally, so the Regions list must **filter tags** created by them (prefix
  `orientation-` / `plane-`) to avoid confusion.
- **Scalar color-by-values with raw numeric arrays** — `set_color_by_values` with an
  arbitrary array needs a data loader/table editor; that stays on the API/add-on. The
  GUI offers instead **color-by-existing-attribute** (§8), which needs no external data.
- **Add-on `Basic` region tooling** — postponed, like the selection add-on side.

---

## 3. Interaction model — the region lifecycle

Regions are persistent objects; the subpanel is a manager over `view.regions`. The
lifecycle it exposes:

- **Birth:** every creation path resolves an atom set (query / active selection /
  split / complement / boolean) and calls `new_region(...)`. Naming follows the same
  **collision policy** as the Selection subpanel — the backend raises on a duplicate
  tag, and the UI offers **Rename / Overwrite / Cancel** (programmatic paths may
  auto-increment). Selections and regions are **separate registries**, so a selection
  and a region may share a name.
- **Life:** represent (style composer), show/hide, isolate, focus, rename, inspect.
  Composition and complement create **new** regions (never mutate operands in place).
- **Death:** delete removes the Mol\* component and unregisters the tag.

**Boolean vocabulary.** Union (∪) / Intersection (∩) / Difference (A − B) reuse the
exact naming of the selection set-operations, so a user who learned one learns the
other. Difference is **ordered** (A − B ≠ B − A); the composer makes the order explicit.

**Relationship to selection.** The `→ Region` promote bridge in the Selection subpanel
already creates a region from the active/saved selection. This subpanel is where those
regions then live and are managed; it does not duplicate the promote flow, it
**receives** its output and adds region-native creation on top.

---

## 4. Design — subpanel layout

Vertical stack inside the Studio → Regions content area. Four blocks:

### A. Create & global actions (top)

- **Create region** (collapsible composer) with three origins:
  - **From active selection** — `Create from active selection` → `new_region_from_active_selection`.
    Disabled when there is no active selection (read `currentSelection.count_atoms`).
  - **From query** — the **shared query composer** (MolSysMT / Indices) with **manual
    verification** (a `Check` button / `Enter`; `idle` while typing, **no** per-keystroke
    preview) → `new_region(selection=…, syntax=…)`. See §6.1: it is a shared component
    implementing this model, which the paused Selection refinements inherit (Option B).
  - **Split by hierarchy** — dropdown `chain | molecule | entity` + `Split` →
    `make_regions_by(element)` (one named region per element; chains use their label,
    others `element_index`).
  Optional name field (collision policy above) and an optional initial representation.
  **Naming on batch creation:** single creations use the interactive collision policy
  (Rename / Overwrite / Cancel); **batch** creation (`make_regions_by`) instead
  **auto-increments** conflicting tags silently (`A`, `A__2`, …) so one collision never
  aborts a many-region split or forces a prompt per element. This is already the backend
  behaviour — `_split_into_regions` resolves each tag through `_unique_region_tag`
  (`viewer/regions.py`) — so the UI must simply **not** raise the collision dialog for
  the split path.
- **Global actions:** `Show all` / `Hide all` — **one action → one public method → one
  event**: a single `show_all_regions` / `hide_all_regions` action calls the public
  `RegionsManager.show_all()` / `hide_all()` (§6.5) and echoes a **single** consolidated
  summary (batch suppression, §6.6); the frontend never iterates or sends per-region
  messages. Deliberately **not** a global "Reset to default" (that verb has no API and
  ambiguous meaning; per-region reset lives on the card, §8).

### B. Region list (cards)

Each region is a collapsible card. Header:

- **Tag** (click = camera `focus`), **atom count**, **representation/preset** hint, a
  **visibility** toggle (👁, `show`/`hide`), and **delete** (🗑).
- A **⚠ overlap** badge when this visible region shares atoms with another visible
  represented region (from the backend, §6.2). Clicking it opens the **Boolean
  composer (§4C) pre-filled with Difference** between the two overlapping regions — an
  explicit, non-destructive way to resolve z-fighting (never automatic).

Quick actions band:

- **Isolate** (`show_only`) — hide everything else, show only this region.
- **Complement** (`new_complementary_region`) — create the inverse region.
- **Rename** — explicit inline form (collision policy). *Not* bound to a
  double-click on the focus label, to avoid click/focus races.
- **Duplicate** (§8) — clone atoms + representation under a new tag.
- **Reset representation** (§8) — revert this region to the base representation.

Expandable **Style composer** (faithful to the API):

- **Representation** select — the **12** real types (`view.representations`), not 5.
- **Preset** select — `view.presets` (built-ins + user presets).
- **Opacity** slider — `alpha` `[0,1]`. The numeric readout updates live on `input`; the
  `set_region_representation` message is **fired on `change` (mouseup)** — one message when
  the drag ends — so it never floods the kernel IPC. (An optional light throttle can be
  added later if live 3D feedback during the drag is wanted; `change`/mouseup is the safe
  default.) This is a **different** mechanism from the query composer's manual verification
  (§4A): a slider's intermediate values are all valid, so the concern is throughput, not
  incomplete-input noise.
- **Quality** dropdown — `quality` enum (for large-system performance).
- **Color** — scheme (element / chain / secondary-structure / hydrophobicity),
  **uniform color** picker, and **color by attribute** (§8; e.g. bfactor / occupancy /
  charge) — the dropdown lists **only attributes actually present** in the loaded system
  (§6.2 availability flags), so formats without them (`.xyz`, `.gro`, `.xtc`, …) never
  offer a missing attribute — plus **reset colors**.

### C. Boolean composer (bottom)

`Region A ▾` · `∪ Union | ∩ Intersection | − Difference (A−B) ▾` · `Region B ▾` (or multiple checkbox/selection for subtracting/combining multiple regions) · optional output name → `Create`. Populated from the live region list (refreshed on create/delete/rename).
* **Multi-operand / Multilayer Composition:** To prevent manual cascading steps for complex subtraction/union formulas, Union and Difference operations support selecting multiple target regions. For example:
  * Base: `site_A`
  * Operator: `− (Difference)`
  * Subtrahends (multi-selection): `[x] backbone`, `[x] water`
  * Backend evaluation: `indices_A - (indices_B | indices_C)`.
* Produces a **new** region via the corresponding API composition calls. Worked example: `pocket ∖ (backbone | water) → pocket_sidechains`.

### D. Inspection (per card, on demand — lazy)

A collapsible metadata panel per region backed by `region.info()` + `region.get_center()`:
atom/element composition (n atoms, n groups/chains), molecular composition, geometric center, and **provenance details**. Gives the GUI what today needs `region.info()` / `get_center()` in Python.

**Lazy + frame-accurate.** These metrics are **not** carried in the static region
summary (they are expensive, and a centroid changes per trajectory frame). Instead they
are fetched **on demand** when the `ⓘ` panel is expanded, via a `get_region_details {tag}`
request-response (§6.2), and the centroid is resolved **in the current playback frame** so
it matches what the user is looking at — without polluting the socket during normal
playback.

**Provenance / Trazabilidad:** Exposes a clear text description of the region's origin based on its saved creation details:
* *Query-based:* `Origen: Consulta (MolSysMT) → "molecule_type == 'protein'"`
* *Selection-based:* `Origen: Selección Activa`
* *Split-based:* `Origen: División por cadena (Chain A)`
* *Complement-based:* `Origen: Complemento de backbone`
* *Boolean-based:* `Origen: Composición → site_A − (backbone | water)`

---

## 5. Reproducibility / provenance

Lighter than selections. A `Region` already stores its defining `selection` expression
(`self.selection`) and `atom_indices`.

> **(proposed — not implemented.)** An earlier revision of this document asserted that
> "regions store their origin kind and parameters in `_provenance` metadata". They do not:
> `grep -rn "_provenance" molsysviewer/` returns nothing. Provenance is specified in
> `region_contracts.md` §C.1 and delivered in Phase 3 of the implementation plan.
>
> **(proposed.)** Regions also do **not** currently survive export/replay in any meaningful
> sense: `viewer/state.py` persists only `{tag, atom_indices}` per region, losing
> representation, preset, params, visibility, colours and the defining expression, and it does
> not filter transient `focus`/`orientation`/`plane` tags on export. Full serialisation is
> `region_contracts.md` §C.2, delivered in Phase 3.

Targets:

- **Query-created** regions keep their `(expression, syntax)` so they can re-evaluate
  across rebuild/topology change (the field already exists on the object; ensure the
  create-from-query path stores it rather than only indices).
- **Interaction/selection-created** regions replay by **remapping indices** via
  `atom_index_map` during `apply_system_edit`, like selections.
- **Composed / complement / split** regions store their recipe informally through their
  atom sets; exact re-derivation across large topology edits is **best-effort** (same
  R3 honesty as selections). No live/per-frame regions.

Representation state (type/preset/alpha/quality/color) is part of the region object and
is re-sent on rebuild through the existing region messages.

---

## 6. Architecture / How

### 6.1 Frontend (`molsysviewer/js/src/ui/panels/regions-panel.ts`)

> Path corrected 2026-07-10. The panel no longer lives in `group-panel.ts`: the Studio A–F
> refactor moved each subpanel to its own module under `ui/panels/`, and
> `renderRegionsSection()` no longer exists. Rendering happens in `RegionsPanel.paint()`.

The panel grows from the old flat list to the A/B/C/D layout,
reusing existing helpers (`makeSectionHeader`, `makeRowElement`, `makeButton`,
`makeStyledSelect`, `renderStyleComposer`) and the collision/rename idioms. The
create-from-query path uses a **shared query-composer component** with **manual
verification** (`Check` / `Enter`, `idle` while typing — no per-keystroke preview),
extracted so the paused Selection refinements inherit the same component (Option B; §4A).
New panel actions route through the existing
`onAction(action, details)` channel (today it already carries `delete_region`,
`toggle_region_visibility`, `rename_region`, `set_region_representation`,
`create_region_from_selection`, `focus_region`).

### 6.2 Backend (`molsysviewer/viewer/core.py` frontend-event handlers)

New ops resolve on the Python side so provenance/naming are known there, and each **routes
through a public API method** (existing or newly added in §6.5) — never a private helper or
open-coded logic. Each echoes an updated region summary so the list stays in sync.

- `create_region_from_query {expression, syntax, tag?, representation?}` →
  `view.new_region(selection=expression, syntax=syntax, tag=…, representation=…)`
  (store the expression for §5).
- `make_regions_by {element, selection?}` → `view.make_regions_by(element)`.
- `show_only_region {tag}` → `view.regions[tag].show_only()`.
- `create_complementary_region {tag, new_tag?}` →
  `view.regions[tag].new_complementary_region(tag=new_tag)`.
- `compose_regions {tag_a, tag_b, op, new_tag?}` →
  `view.regions[tag_a].union|intersection|difference(view.regions[tag_b], tag=new_tag)`.
- `reset_region_representation {tag}` → revert to the base representation (§8).
- `color_region_by_attribute {tag, attribute, palette?}` → resolve the attribute via
  `msm.get` and call `region.set_color_by_values(...)` (new helper, §8).
- `duplicate_region {tag, new_tag?}` → `new_region` with the same `atom_indices` and a
  copy of `repr_params` (§8).
- `show_all_regions` / `hide_all_regions` → `view.regions.show_all()` / `hide_all()`
  under the batch-update suppression of §6.6 (one consolidated summary, no per-region
  flicker).
- `get_region_details {tag}` — **request-response** for the lazy inspection panel (§4D):
  resolve `region.info()` composition + `region.get_center(structure_indices=<current
  frame>)` and return them for that one card only (no broadcast, no polling during
  playback). The centroid is computed in the **current playback frame**.
- **Region summary payload:** extend `RegionSummary` (today `{tag, atom_count,
  hidden}`) with `representation`, `preset`, and `overlap_tags` (from `Region.overlaps()`,
  §6.5) so the card can show the representation hint and the ⚠ badge. It also carries
  **structural-attribute availability flags** (`available_attributes`, e.g.
  `["bfactor", "occupancy"]`) — computed once at load/summary time by probing which
  attributes exist in `_molsys` — so the "Color by attribute" dropdown (§4B) exposes only
  present attributes and never offers a missing one (P3). Expensive per-region metrics
  (centroid, composition) are **not** in the summary — they are fetched lazily via
  `get_region_details` above.

Existing (reused, no change): `create_region_from_selection`,
`create_region_from_saved_selection`, `delete_region`, `toggle_region_visibility`,
`rename_region`, `set_region_representation`, `focus_region`.

**Implementation note — use MolSysMT's attribute inventory, then validate values.**
The current MolSysMT API provides `msm.get_attributes(..., include_none=False)`, which
reports populated attributes for the loaded form. Use it to gate the candidate scalar
attributes (`b_factor`, `occupancy`, `partial_charge`, `formal_charge`); the actual
coloring call still reads the selected values and rejects missing/non-scalar data.

```python
CANDIDATE_ATTRS = ["b_factor", "occupancy", "partial_charge", "formal_charge"]
present = set(msm.get_attributes(view._molsys, include_none=False,
                                 output_type="list", skip_digestion=True))
available = [attr for attr in CANDIDATE_ATTRS if attr in present]
# -> available_attributes in the region summary payload
```

This inventory contract was verified against the local MolSysMT source and real loaded
objects. The value read remains guarded because availability does not guarantee that a
particular scoped subset is numeric and complete.

### 6.3 Representation contract — opacity / quality pass through unchanged (verified)

No protocol change is needed to add opacity and quality. In
`js/src/managers/handlers/state-handlers.ts`, `setRegionRepresentation` computes
`cleanParams = omitStructuralColorKeys(msg.params)` (which strips only color/size-scheme
keys) and passes `typeParams: cleanParams as any` straight to Mol\*. Since Mol\* accepts
`alpha` and `quality` inside a representation's `typeParams`, the backend already
channels `region.set_representation(alpha=…, quality=…)` end to end. The UI only needs
to *send* these params.

> **Correction (2026-07-10).** The same handler — and `createRegion` alongside it — contains
> `const reprType = msg.representation ?? "cartoon";`. A region with **no** representation is
> therefore painted as a cartoon, while Python's `_region_has_visible_representation()`
> believes it has no visual at all. That single fallback is why `reset_representation()`
> never restored the base look, why the opacity slider is inert on a base region, and why
> overlap detection never fired for base regions. It is removed in Phase 1; see
> `region_contracts.md` §A. The pass-through of `alpha`/`quality` described above remains
> correct, but has never been confirmed on screen — that is Phase 6.

### 6.4 Transient/auxiliary regions register as regions (list filter)

Several viewer features create `Region` objects internally that are **not** manageable
chemical regions and must be **filtered out** of the Regions list/summary:

- `show_orientation_axes` / `show_best_fit_plane` → tags `orientation-<n>` / `plane-<n>`
  (geometry overlays; their creation UI lives in Overlays, §2).
- `styles.focus()` → tags `focus<n>` (verified: `styles.py` `_next_focus_tag` →
  `new_region(tag=f"focus{n}")`). These are **ephemeral highlight overlays**, not
  persistent regions; listing them would confuse users (P1).

Filter these transient tags from the summary/list. Automatic geometry tags currently
have the forms `orientation-regionN` / `plane-regionN` (and older/documented
`orientation-N` / `plane-N` forms may exist), while focus tags are `focusN`; use an
exact generated-tag pattern rather than filtering every user tag with those prefixes. (A cleaner
long-term alternative is tagging them with a `kind`/transient flag at creation.)

### 6.5 Public API completeness (new methods to add first)

Per the shared philosophy (§1.3), *managing* is the authority of the **molsysviewer
public API**; every GUI surface must **route through it**, not around it. Several
capabilities this subpanel needs have **no public method today**, so they are added to
the public API **first** (`molsysviewer/regions.py`), and only then wired as `core.py`
event handlers (§6.2). This keeps the API a complete, first-class surface in its own
right (a user must be able to do everything the subpanel does from Python).

New methods on **`Region`** (all `@signal @digest`, index space = `_molsys`, R2):

- `reset_representation()` — clear this region's representation/preset/params and revert
  to the base representation; re-send. (Backs `reset_region_representation`; §8.)
  **Shipped, but broken:** it renders the region as `cartoon` (see §6.3). Repaired in
  Phase 1, where it comes to mean state **None** of `region_contracts.md` §A.1.
- `set_color_by_attribute(attribute, *, element="atom", palette="viridis",
  value_range=None, replace=False)` — resolve an attribute already present in `_molsys`
  (`msm.get(..., **{attribute: True})`) and delegate to the existing
  `set_color_by_values(...)`. The GUI-friendly bridge that avoids raw numeric arrays
  (§8). Guard missing/None values (R4).
- `duplicate(*, tag=None, representation=None, **repr_params)` — create a new region with
  the same `atom_indices` and a copy of the representation/params. (Backs
  `duplicate_region`; §8.)
- `overlaps()` → `list[str]` — public wrapper over the private
  `_overlapping_visual_region_tags`, so the ⚠ badge and any surface can query overlaps
  without reaching into internals.

New methods on **`RegionsManager` / `RegionsMixin`**:

- `show_all()` / `hide_all()` — batch visibility over all managed regions (there is no
  batch call today; the GUI must not open-code the loop). Backs
  `show_all_regions` / `hide_all_regions`.
- `overlaps()` → `dict[str, list[str]]` — tag → overlapping visible tags, for the whole
  registry (optional convenience; the badge can also use `Region.overlaps()`).

**API-only extension decided in Phase 0:** `make_regions_by` accepts
`group | component | chain | molecule | entity`. A group-level split can produce
hundreds of regions, so the subpanel's Split remains restricted to
`chain | molecule | entity`; `group | component` require an explicit Python call.

These additions are the **"make the Python API more complete"** work: without them the
subpanel would be reaching past the public API, which the philosophy forbids.

**(proposed, Phase 4.)** The audit of 2026-07-10 adds to this list: variadic boolean
operators (`a.difference(b, c)`), atomic overwrite for create/rename, complement of several
regions, a `count_regions_by` query to size a split before running it, and — per
`region_contracts.md` — `view.reset_all_colors()`, `Region.provenance`, and the `"inherit"`
representation sentinel.

### 6.6 Batch-update suppression (bulk operations)

Bulk operations — `show_all` / `hide_all` and `make_regions_by` — otherwise emit one
scene message (and one summary rebuild) **per region**, which for 20+ chains causes
visible flicker and IPC lag. The backend batch context suppresses per-item scene
messages and intermediate summary echoes, records one reproducible batch operation,
and emits a **single consolidated summary** at the end. SMonitor `@signal`
breadcrumbs remain active: they are diagnostics, not scene IPC, and suppressing them
would reduce traceability without improving rendering performance.

---

## 7. The surfaces and where this one sits

| # | Surface | Kind | Flavour |
|---|---------|------|---------|
| 1 | molsysviewer public API | programmatic (managing base) | the authority; everything routes through it |
| 2 | **Studio → Regions subpanel** *(this proposal)* | GUI | scene-native region management: create, represent, compose, isolate, inspect |
| 3 | `molsysviewer_molsysmt` add-on | GUI + API | analysis-oriented region use; **postponed** |
| 4 | Selection `→ Region` bridge + canvas right-click | GUI / direct | promotes a selection into a region (`create_region_from_selection`) |

All operate on the **same** `view.regions` registry — a region created anywhere is
managed here.

---

## 8. Non-API additions (new features worth building)

These are not in the Python API today but are cheap, GUI-friendly, and high value; they
are folded into the plan. Each is delivered **first as a public API method** (§6.5) and
only then surfaced in the GUI — the subpanel never reaches past the public API:

- **Color by existing structural attribute** ⭐ — a `Color by: bfactor | occupancy |
  charge | …` dropdown that resolves the attribute already present in `_molsys`
  (`msm.get`) and feeds `region.set_color_by_values(...)`. This gives the most-requested
  "color by B-factor" without any file loader (the salvage of the rejected raw
  color-by-values GUI). New small backend helper + `color_region_by_attribute` op.
- **Reset representation (per region)** — the salvaged, well-defined version of the
  collaborator's ambiguous "Reset to Default": revert **one** region to the base
  representation (clear its params, re-send), not a global reset. New backend op.
- **Overlap → prefilled Difference** — the ⚠ badge, on click, opens the boolean
  composer pre-filled with `A − B` for the overlapping pair; explicit and
  non-destructive (no auto-subtract). Pure UI over the existing `compose_regions` op.
- **Duplicate region** *(nice-to-have, low priority)* — clone atoms + representation
  under a new tag; trivial over `new_region`.

Rejected: a **global "Reset to default"** (no API, ambiguous semantics) and **raw
numeric color-by-values in the GUI** (needs a data loader; stays API/add-on).

---

## 9. Deferred / open

- **Add-on region tooling** and shared-registry integration.
- **Live/dynamic** (per-frame re-evaluated) regions.
- **Automatic Inspect refresh during playback** remains deliberately deferred; the
  panel shows its frame and provides an explicit Refresh action to avoid per-frame IPC.
- **Geometry overlays** UI (in the Overlays subpanel, not here).
- **Representation-specific params** beyond the common set (sizeFactor, ignoreHydrogens,
  …): expose progressively per representation if demand appears; not in the first cut.
- **Auto-resolve overlaps** beyond the prefilled-Difference assist.

---

## 10. Provenance (what was merged and changed)

**Adopted from the collaborator draft:** the three-section skeleton (globals+create /
region cards / boolean composer); per-card **Complement**, **Isolate** (`show_only`),
inline **Rename**; the **12-representation** style composer; the **opacity (alpha)**
slider and **quality** dropdown; the **overlap ⚠ badge**; the phased A/B/C delivery; and
the verified insight that the JS↔Python contract already channels `alpha`/`quality`
via `typeParams` (§6.3).

**Changed / corrected:**

- **"Reset to Default"** (global) — **dropped**; no such API and ambiguous. Replaced by
  a well-scoped **per-region reset representation** (§8).
- **Complement tag** — the API default is `Global-<tag>`, not `<tag>_complement`; the UI
  passes an explicit `new_tag` or uses the API default.
- **Rename** — an explicit affordance, **not** a double-click on the focus label
  (click/focus race).
- **"100% of the API"** — the draft omitted real capabilities; this proposal adds them.

**Added after discussion (maintainer + review):**

- **`make_regions_by` split** (region per chain/molecule/entity) — the highest-value
  creation shortcut, absent from the draft (§4A).
- **Create region from a query** (not only from the active selection), reusing the
  Selection composer (§4A).
- **Inspection** block — `info` + `get_center` (§4D).
- **Geometry overlays → Overlays**, with the Regions-list **tag filter** because they
  register as regions (§2, §6.4).
- **Color by existing attribute**, **overlap → prefilled Difference**, and **duplicate
  region** (§8).
- **Region summary payload** extended with `representation` / `preset` / `overlap_tags`
  (§6.2).
- **Public API completeness** (§6.5) — the new capabilities are added to the public
  `Region` / `RegionsManager` API **first** (`reset_representation`,
  `set_color_by_attribute`, `duplicate`, `overlaps`, `show_all` / `hide_all`), so the GUI
  routes through the API instead of past it, honouring the "managing = public API is the
  authority" invariant. This is the concrete *"make the Python API more complete"* work.

**Integrated from the refinements report (2026-07-09), each verified against code:**

- **Filter `focus<n>` tags** too, not just `orientation-`/`plane-` — `styles.focus()`
  registers highlight overlays as regions (verified `styles.py`); they must not appear as
  manageable regions (§6.4). *(report P1)*
- **Opacity slider fired on `change`/mouseup** — live numeric readout on `input`, but the
  IPC message only on release, so dragging never floods the kernel; `change`/mouseup is the
  default over a debounce (§4B). *(P2, refined 2026-07-09)*
- **Attribute-availability gating** — "Color by attribute" lists only attributes present in
  the loaded system, via summary flags (§4B, §6.2); corrected the report's `msm.get(select=…)`
  mechanism to a load-time availability probe. *(P3)*
- **Batch naming = auto-increment** — documented as the split rule; **already** implemented in
  the backend (`_split_into_regions` → `_unique_region_tag`, verified), so the UI just must not
  prompt on the split path (§4A). *(P4 — no new backend work)*
- **Lazy, frame-accurate inspection** — centroid/composition fetched on demand via
  `get_region_details {tag}`, centroid in the current playback frame, kept out of the static
  summary (§4D, §6.2). *(P5)*
- **Batch-update suppression** — a backend batch context collapses per-item signals into one
  consolidated summary for `show_all`/`hide_all`/`make_regions_by`; medium-priority
  optimisation for large systems (§6.6). *(P6)*

**Cross-subpanel decisions (2026-07-09):**

- **Query composer = manual verification (Check/Enter), shared component (Option B).** The
  Selection refinements (`studio_selection_subpanel_refinements.md`, paused) found the
  per-keystroke debounced preview harmful (a query is incomplete while typing → constant
  false "✗ invalid syntax" + kernel overhead). Region therefore does **not** reuse the
  current debounced composer; it implements the manual-verification composer as a **shared
  component**, and the paused Selection refinement (its Part A) will **inherit** it when
  resumed (§4A, §6.1).
- **Show / Hide all = one action → one public method → one event** (§4A) — no frontend
  iteration; the stale "iterate / no batch API" wording is retired now that §6.5 adds the
  public `show_all()` / `hide_all()`.
- **Collision behavior is explicit** — `new_region(tag=...)` raises if the tag already
  exists; interactive overwrite is delete-then-create. This replaces the former silent
  registry overwrite.
- **`RegionsManager` is viewer-bound** — it is constructed internally as
  `RegionsManager(view)`, enabling its public batch methods to use the owning transport.
- **Opacity slider = fired on `change`/mouseup** by default (§4B) — a slider is a *different*
  failure mode from the query composer (all values valid → throughput, not incomplete-input
  noise), so `change`/mouseup is correct here even though per-keystroke debounce was wrong
  for the query.
