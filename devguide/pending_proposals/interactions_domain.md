# Proposal: `Interactions` — a scene domain for derived atom–atom relations

**Status:** approved (design finalized 2026-07-20). Ready for step-by-step implementation.

**Verdict: yes — a domain of its own, with its own Studio subpanel.** An interaction has a *shape* (graph edges over frames) that no existing domain has.

**Sequencing: after the scene-objects block.** It inherits every contract that block establishes (T, S0, S1, S4, S5, S6, S7, V).

---

## 1. What a user wants

> "Show me the hydrogen bonds between the ligand and the pocket. Show me this
> disulfide bridge. Show me the π-stacking between these two rings — and tell me
> whether it survives the trajectory."

---

## 2. What exists today, and why it is not enough

**`view.shapes.links.add_hbonds(structures=[...])`.** Read the signature: the
caller must **pre-compute the donor/acceptor pairs for every frame** and hand them
over as a list indexed by structure. The API draws cylinders where it is told; it
computes nothing. `add_interaction_sites(centers=…, kinds=…)` is the same.

So today an interaction is **a drawing, not an object**. What is lost: the recipe,
the criterion (§3), the per-frame re-evaluation, and the identity — it cannot be
renamed, hidden, layered, serialised or undone as an interaction, only as the
anonymous shape it degenerated into.

---

## 3. Decision: Calculation Engine & Reproducibility

### 3.1 Primary Engine: MolSysMT computes. Mol\* draws.

**A hydrogen bond is not a fact; it is a criterion.** MolSysMT ships multiple criteria:
```python
molsysmt/hbonds/get_buch_hbonds.py
molsysmt/hbonds/get_luzard_chandler_hbonds.py
```
So *"the hydrogen bonds of this pocket"* is not well defined until the criterion
and its cutoffs are named. A viewer whose guiding principle is that scientific
results remain reproducible **must record which criterion produced the figure** —
and that record is exactly `provenance` (Contract R).

**Default Engine (`engine="molsysmt"`):** The criterion lives in MolSysMT for:
1. **Reproducibility:** A named, versioned, citable criterion with its cutoffs
   serialised in the session.
2. **Flexibility & Reuse:** New or parameterised definitions are added where scientific
   code belongs; the viewer needs no change to gain them.

### 3.2 Optional Engine: `engine="molstar"`

When interactive speed is paramount, the user can select `engine="molstar"`. Mol\* executes
its GPU/JS contact computation engine (`ComputeContacts`) directly in the browser or Node.js runtime,
sending the resulting edge list back to Python.

---

## 4. Input Modes: Three Data Sources

An `InteractionSet` can be populated from three distinct sources:

### Mode A: Criterion-Based (Dynamic or Static Calculation)
Calculated automatically per frame via MolSysMT or Mol\*:
```python
view.interactions.add(
    kind="hbond",
    selection_a="molecule_type==protein",
    selection_b="molecule_type==small_molecule",
    criterion="luzar_chandler",
    cutoffs={"distance": "3.5 angstroms", "angle": "30 degrees"},
    engine="molsysmt",  # "molsysmt" | "molstar"
    mode="dynamic",     # "static" | "dynamic"
    tag="site_hbonds",
)
```

### Mode B: Explicit Per-Frame Pair Mapping
Pre-calculated atom pairs provided directly by user scripts:
```python
user_pairs = {
    0: [(3, 105), (3, 108), (12, 204)],
    1: [(3, 105), (12, 204)],
    2: [(3, 105), (3, 108)],
}

view.interactions.add(
    kind="hbond",
    pairs=user_pairs,
    tag="custom_script_hbonds",
)
```

### Mode C: Pandas DataFrame / File Input
Imported from third-party tools (e.g. ProLIF, PLIP, GetContacts):
```python
view.interactions.add(
    kind="hbond",
    dataframe=df_prolif,  # columns: frame, atom_a, atom_b, interaction_type
    tag="prolif_hbonds",
)
```

---

## 5. Terminology Alignment: `persistence` (not `occupancy`)

> ⚠️ **Term Decision (2026-07-20):** The term `occupancy` is avoided for interaction persistence
> to prevent collision with crystallographic PDB occupancy (`atom.occupancy` in `molsysmt.Topology`).

The metric measuring the fraction of trajectory frames ($[0.0, 1.0]$) in which a specific contact/edge exists
is named **`persistence`** (or `contact_persistence`).

- `view.interactions.persistence(tag)` — returns the per-edge fraction of frames in which each bond exists.
- `view.interactions.count_series(tag)` — returns the total interaction count per frame as a `puw` array.

---

## 6. Mol\* Native Realisation & Kind Mapping (`renderer="native"`)

Mol\* (extension `extensions/interactions`) separates computation from rendering by design:
```js
ComputeContacts    : Structure.Selections → InteractionData   // Mol* computes
CustomInteractions : Root, params.interactions → InteractionData   // YOUR list; computes nothing
InteractionsShape  : InteractionData → Shape.Provider          // rendering
```

### 6.1 Vocabulary Projection
Mol\* ships 10 native interaction kinds: `hydrogen-bond`, `weak-hydrogen-bond`, `ionic`, `pi-stacking`, `cation-pi`, `halogen-bond`, `hydrophobic`, `metal-coordination`, `covalent`, `unknown`.
- Scientific interaction types from MolSysMT, ProLIF, or PLIP are mapped to Mol\*'s nearest visual kind.
- Unmapped or custom types default to `"unknown"` (which renders cleanly with custom colors).

---

## 7. Integration with Existing Scene Contracts

### 7.1 Layer Membership (Contract S4)
`InteractionSet` objects carry `layer_tag` and integrate seamlessly with `view.layers`. Hiding or showing a layer in the **Layers** subpanel cascades to all contained interaction sets.

### 7.2 System Edits & Broken State (Contract S7)
During `apply_system_edit`:
- Mode A (Criterion) dynamic sets are re-evaluated against the new topology.
- Mode B & C (Explicit) pairs are remapped via `atom_index_map`. If any pair references an atom removed from the system, the `InteractionSet` marks `broken=True` with a clear `broken_reason` and displays a `⚠` badge in Studio.

### 7.3 Session State & Serialization (Contract S5)
In `export_state`, an `InteractionSet` serializes its source recipe (criterion, cutoffs, selections, or explicit pairs mapping), style properties (`color`, `style`, `radius`), visibility, and `layer_tag`.
Transient interaction sets (prefixed with `_TRANSIENT_INTERACTION_TAG`) are filtered out during export.

---

## 8. Studio Subpanel Integration (`interactions-panel.ts`)

The domain gets its own Studio subpanel (**Interactions**) alongside Regions, Whole, Shapes, Measures, Annotations, and Layers.
- Displays listed **`InteractionSets`** (recipes/sources, not individual thousand-edge lines).
- Shows per-set summary: active frame count, criterion/source provenance, and interactive persistence sparklines.
- Provides visual controls: `color`, `style` (`solid` / `dashed`), and `radius`.

---

## 9. Summary of API Surface

```python
# Canonical manager surface (S0)
view.interactions.add(...)
view.interactions.get(tag)
view.interactions.info(tag=None)
view.interactions.show(tag)
view.interactions.hide(tag)
view.interactions.delete(tag)
view.interactions.clear()

# Analytics
view.interactions.persistence(tag)      # per-edge fraction of frames (0.0 to 1.0)
view.interactions.count_series(tag)   # interaction count per frame
```
