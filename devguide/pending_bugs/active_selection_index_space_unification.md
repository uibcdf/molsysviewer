# Bug + plan: unify the runtime on the `_molsys` index space

**Status:** open — plan agreed, not implemented.
**Severity:** foundational (index-space convention across selection / interaction /
regions). Currently causes a concrete failure (h5py, below) plus pervasive complexity.

---

## 1. The bug (foundational)

The Python runtime treats the **original input system** (`view.molecular_system`) as the
canonical index space for selections, and the **loaded system** (`view._molsys`, a
`molsysmt.MolSys`) / frontend as a *local* space, bridged everywhere by an
`IndexMapper`. This is an **inverted default**.

- `view.molecular_system` is the raw input the user passed to `load()` — often a **file
  form** (the demos are `file:h5msm`). It is provenance ("where we came from").
- `view._molsys` is the system actually loaded, converted to an in-memory
  `molsysmt.MolSys`, and rendered by the frontend. It is the system the user **sees and
  works on**; atom `0` is the atom the user sees as `0`.

Making the *original* the working space taxes every operation with a local↔original
mapping, keeps an `IndexMapper` even for full loads (identity), and forces topology
queries against the raw input form.

### Why it was (probably) chosen — and why it is wrong

Plausible rationale: original indices are **absolute/stable** (independent of which
subset is loaded) and mirror `msm.select(user_input, …)`, so a selection is a durable
reference to the user's real atoms. Coherent — but the wrong **default** for a viewer:
the working reality is the *loaded* system. The stability property is rarely needed and
is **recoverable on demand** via the mapper. It should have been opt-in reference, not
the pervasive working space.

### Concrete symptom (the failing test)

`active_selection.set` computes metadata with
`msm.get(view.molecular_system, element="atom", selection=<unsorted indices>, group_index=True)`.
When `molecular_system` is `file:h5msm`, h5py fancy-indexing requires **increasing
order** → `TypeError: Indexing elements must be in increasing order`
(`tests/test_selections.py::test_selection_frontend_actions`, via
`compose_saved_selection op=add`). Root cause is not "unsorted indices" — it is
**querying the original file form at all**.

Related smell: `view._index_mapper is not None` even for a **full** demo load (identity
mapper), so the "query original" branch fires needlessly in the common case.

---

## 2. Decision

**`_molsys` is the single canonical, functional index space — on BOTH axes.** All
`atom_indices` **and** `structure`/frame indices — the Python API, the frontend, and
what the user sees — are `_molsys` indices. `view.select`, every selection/interaction
operation, and the trajectory frame index resolve **against `_molsys`**. (The structure
axis has the *same* inverted default today: `_current_structure_index` is stored in
original-frame space and mapped to local for the player — `core.py:1148-1152`,
`1745-1750`. It gets the same treatment as atoms.)

`view.molecular_system` and the original-index mapping stay only as **provenance /
reference**, recoverable on demand — never in the functional path.

**Mapper invariant (no identity mappers).** There are **two independent mappers**:
`_atom_index_mapper` and `_structure_index_mapper`. The **atom** mapper is `None` when
*all* atoms are loaded; the **structure** mapper is `None` when *all* structures are
loaded. Each exists **iff** its axis is a genuine subset, and each is kept purely as
reference — never consulted in the functional path.

**Out of scope (do not touch):**
- **`apply_system_edit`** reconciliation (`atom_index_map`, `core.py:1543-1550`) — the
  old↔new `_molsys` remapping across edits is unaffected (it operates in whatever space
  `_molsys` uses).

**Property — Python-only.** The frontend already operates in `_molsys` space (its
payload comes from `_molsys.to_form("ViewerJSON")`), so this migration touches **no TS /
`viewer.js`** and needs **no rebuild**. It is entirely a Python-runtime change.

---

## 3. Touch points (verified)

All ATOM-space local↔original conversions to remove / redirect to `_molsys`:

| # | Location | Today | Target |
|---|----------|-------|--------|
| 1 | `viewer/molsysmt_interface.py` `select()` (~363-411) | queries `molecular_system` + filters when mapper present | always `msm.select(self._molsys, …)` — drop the original branch |
| 2 | `viewer/core.py` `_active_selection_query_system` (535-544) | returns `molecular_system` (original) | return `(self._molsys, atom_indices, False)` |
| 3 | `viewer/core.py` `_expand_selection_action` (596-597) | `to_original_atoms` on the result | drop — result stays `_molsys`-space |
| 4 | `viewer/core.py` `interaction_active_selection_changed` (995-1013+) | frontend local atoms → `to_original_atoms`; query original | store local atoms as-is; query `_molsys` |
| 5 | `viewer/core.py` `_enrich_interaction_payload` (1272-1274) | `to_original_atoms(raw)` | keep `raw` (local `_molsys`) |
| 6 | `active_selection.py` `set()` (162-235) | queried `molecular_system`; `to_local_atoms` for frontend; only `group_indices` | query `_molsys`; send atoms as-is; **all** levels *(already drafted in the working tree — fold in)* |
| 7 | `viewer/regions.py` (259, 266) | `to_original_atoms(local_indices)` | keep `_molsys`-space; region indices are `_molsys` |
| 8 | `viewer/core.py` `trajectory_frame_changed` (1148-1152) | frontend frame → `to_original_structure`; stores original-frame | store the frontend frame as-is (`_molsys`-frame) |
| 9 | `viewer/core.py` `_local_structure_index_for_player` (1745-1750) | `to_local_structure(_current_structure_index)` | `_current_structure_index` is already `_molsys`-frame → return as-is |
| 10 | `loaders/load_molsysmt.py` (56) | always builds a full `IndexMapper` | build per-axis mapper(s), `None` when that axis is full (§2 invariant) |

### Downstream consequences (by construction, once 1–10 land)

- **Regions & saved selections** store `_molsys`-space atom indices (they inherit from
  `active_selection`: `core.py:653`, `:787`). Region-tag matching in `_enrich`
  (`:1281`) stays consistent because picks are now `_molsys`-space too.
- **`IndexMapper` (atoms)** drops out of the hot path; retain only as an optional
  reference to recover original indices on demand (or replace with a stored
  `original_atoms` array). Decide in §5.

---

## 4. Semantic decisions to lock before coding

1. **`view.select` public contract changes** to return `_molsys`-space indices. Confirm
   no addon / doc / notebook depends on original-space results. (grep the addon repo +
   docs.)
2. **Expand-beyond-loaded:** with `_molsys`-only, "expand to whole chain" can only reach
   atoms **present in the loaded subset**. Under the old original-query it could include
   *unloaded* atoms. Decision: **expansion is limited to the loaded system** (you can
   only select what is loaded/visible). Document it.
3. **Mapper construction changes** (per the §2 invariant): `load` builds the **atom**
   mapper only when atoms are a subset, and the **structure** mapper only when structures
   are a subset — `None` otherwise (no identity mappers). Kept purely as reference
   (recover original indices on demand); the functional path never consults it. *This
   supersedes any "leave `load` untouched".*
4. **Both axes symmetric:** `view.select` resolves **all** elements against `_molsys`
   (atoms **and** `structure` indices → `_molsys`); the trajectory frame index is
   `_molsys`-space too (`trajectory_frame_changed`, `_local_structure_index_for_player`).
   **Verify** no caller of `view.select(element="structure")` or of the player expects
   original-frame indices before landing.

---

## 5. Test impact

Expect updates (they encode the old original-space contract):

- `tests/test_active_selection.py` — `test_context_action_expand_selection_respects_subset_loaded_index_mapper`
  and siblings: expectations flip to `_molsys`-space (e.g. `active_selection.atom_indices`
  becomes `[0]`, not `original_group_atoms`). Rename/retarget the "respects original index
  mapper" premise.
- `tests/regions/test_region_flow.py` — any subset case asserting original-space region
  indices.
- `tests/molsysviewer/test_molsysview_load.py` — subset-load index assertions.
- `tests/test_index_mapper.py` — the mapper's own math still holds; drop only assertions
  that require it in the *selection* path.
- `tests/test_selections.py::test_selection_frontend_actions` — should pass once metadata
  is computed against `_molsys`.

---

## 6. Implementation plan (phased)

**Phase 0 — lock decisions.** Confirm §4 (1) `view.select` becomes `_molsys`-space,
(2) expand is limited to the loaded system, (3) mapper kept reference-only,
(4) `view.select` structure axis → `_molsys`. `grep -rn` the addon repo + docs +
notebooks for any reliance on original-space `view.select` results.

**Atomicity (read first).** The runtime must stay coherent: a *half*-migrated state
mixes index spaces and **is expected to be red** (that is exactly today's tree). So the
**code** changes (Phases A + B) and the **test** updates (Phase C) land as **one atomic
commit**, executed in the order below; the full suite is only expected green after
Phase C. Do not stop mid-way. Python-only — no `viewer.js` rebuild.

### Phase A — Producers → `_molsys` *(no independent green; verify by reasoning)*

Everything that *emits* atom indices must produce `_molsys` space.

- [ ] **A1** `view.select` (`molsysmt_interface.py`) → always `msm.select(self._molsys,
      …)` for all elements; delete the `molecular_system`-query + filter branch.
- [ ] **A2** `_active_selection_query_system` (`core.py:535`) → `return (self._molsys,
      atom_indices, False)`.
- [ ] **A3** `interaction_active_selection_changed` (`core.py:995`) — ⚠️ **highest-risk
      step** (it also builds `group_indices` + `region_tags`): store the frontend's atoms
      as-is (`_molsys`); compute the level indices via `msm.get(self._molsys, …)`; delete
      every `to_original_atoms` / `to_local_atoms`.
- [ ] **A4** `_enrich_interaction_payload` (`core.py:1272`) → keep `raw` atoms; delete the
      `to_original_atoms`; region-tag matching is now `_molsys` vs `_molsys`.
- [ ] **A5** `regions.py` (259, 266) → region indices stay `_molsys`; delete
      `to_original_atoms`.
- [ ] **A6** Structure axis: `trajectory_frame_changed` (`core.py:1148`) stores the
      frontend frame as-is (`_molsys`-frame, no `to_original_structure`);
      `_local_structure_index_for_player` (`core.py:1745`) returns
      `_current_structure_index` as-is (no `to_local_structure`).
- **Phase-A check (reasoning + grep, not the suite):** no `to_local_atoms` /
  `to_original_atoms` / `to_local_structure` / `to_original_structure` /
  `molecular_system` remain in the *functional* path (only `apply_system_edit`'s
  `atom_index_map` stays).

### Phase B — Consumers → `_molsys` *(lands together with A)*

- [ ] **B1** `active_selection.set` — finish the `_molsys` rewrite already in the tree:
      resolve via `msm.select(_molsys, …)`, **all five** levels from `_molsys`, send atoms
      as-is (no `to_local_atoms`).
- [ ] **B2** `_expand_selection_action` (`core.py:596`) → drop the `to_original_atoms`
      remap; the result stays `_molsys`.
- [ ] **B3** Split `_index_mapper` into **two independent mappers**
      (`_atom_index_mapper`, `_structure_index_mapper`), each `None` on its own; update
      every call site (`molsysmt_interface.py`, `core.py`, `regions.py`,
      `loaders/load_molsysmt.py`) to the axis-specific mapper.
- [ ] **B4** `load` (`load_molsysmt.py:56`) builds `_atom_index_mapper` **only** when
      atoms are a subset, and `_structure_index_mapper` **only** when structures are a
      subset — `None` otherwise (§2 invariant). Kept as reference; not consulted in the
      functional path.

### Phase C — Tests + docs + verify *(brings the suite back to green)*

- [ ] **C1** Update the tests encoding original-space (§5) to `_molsys` — notably
      `test_..._respects_subset_loaded_index_mapper` (expect `[0]`, not
      `original_group_atoms`) and rename its premise.
- [ ] **C2** Docs: `view.select` returns `_molsys`-space; expansion is limited to the
      loaded system (§4.2).
- [ ] **C3** **Verify green:** `python -m pytest tests/ -q` **and** `npm run test:js`
      (no rebuild — Python-only). Assert: `test_selection_frontend_actions` passes, **no
      h5py error**, and a final `grep` shows **no `molecular_system` query** on the hot
      path.

### Landing

One commit, Phases A+B+C together (the code is atomic; the test updates make it green).
Suggested message:
`fix(selection): unify the runtime on the _molsys index space (drop original-space default)`.

## 7. Current tree state

The `active_selection.set` `_molsys` rewrite (Phase **B1**) is already in the working
tree, which is why the suite currently shows **2 failures** — a half-migrated state
(`set` is `_molsys`-space; the producers are still original-space). This is the expected
"red mid-migration" state. Land Phases A + C to make it coherent; do **not** revert B1 —
complete the migration.
