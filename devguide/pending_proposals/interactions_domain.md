# Proposal: `Interactions` — a scene domain for derived atom–atom relations

**Status:** proposed (2026-07-12), with the key decisions **taken** (§3, §4, §6).
Assessment requested by the maintainer while evaluating the scene-objects block.

**Verdict: yes — a domain of its own, with its own subpanel.** Not because a panel
would be convenient, but because an interaction has a *shape* no existing domain
has.

**Sequencing: after the scene-objects block.** It inherits every contract that
block establishes (T, S0, S1, S5, S6, V). Built earlier, it would be rebuilt.

---

## 1. What a user wants

> "Show me the hydrogen bonds between the ligand and the pocket. Show me this
> disulfide bridge. Show me the π-stacking between these two rings — and tell me
> whether it survives the trajectory."

## 2. What exists today, and why it is not enough

**`view.shapes.links.add_hbonds(structures=[...])`.** Read the signature: the
caller must **pre-compute the donor/acceptor pairs for every frame** and hand them
over as a list indexed by structure. The API draws cylinders where it is told; it
computes nothing. `add_interaction_sites(centers=…, kinds=…)` is the same.

So today an interaction is **a drawing, not an object**. What is lost: the recipe,
the criterion (§3), the per-frame re-evaluation, and the identity — it cannot be
renamed, hidden, layered, serialised or undone as an interaction, only as the
anonymous shape it degenerated into.

## 3. Decision: **MolSysMT computes. Mol\* draws.**

**A hydrogen bond is not a fact; it is a criterion.** MolSysMT already ships two,
and they return **different sets of bonds on the same structure**:

```
molsysmt/hbonds/get_buch_hbonds.py
molsysmt/hbonds/get_luzard_chandler_hbonds.py
```

So *"the hydrogen bonds of this pocket"* is not well defined until the criterion
and its cutoffs are named. A viewer whose guiding principle is that scientific
results remain reproducible **must record which criterion produced the figure** —
and that record is exactly `provenance` (Contract R).

**Decision (2026-07-12): the criterion lives in MolSysMT, never in the viewer and
never in Mol\*.** Reasons, in order of weight:

1. **Reproducibility.** A named, versioned, citable criterion, with its cutoffs
   serialised in the session.
2. **Flexibility.** New or parameterised definitions are added where scientific
   code belongs; the viewer needs no change to gain them.
3. **Reuse.** The whole ecosystem gets them — an H-bond computed in MolSysMT is
   useful in an analysis with no viewer attached.

**Accepted cost (explicitly, by the maintainer):** an *interactive preview* —
dragging a cutoff slider and watching the bonds change in real time — will be slow
through the Python round-trip. That bridge gets crossed when we reach it. What we
do **not** do is quietly fall back to Mol\*'s engine for the preview: that would
install a second, unauditable source of truth (Contract S1), and the fast path
would be the one that lies.

## 4. Mol\* draws them natively — **and we do not have to use its engine**

This was the open question, and the answer is the best possible one. Mol\*
(extension `extensions/interactions`, 2025) **separates computation from
rendering by design**. Three state transformers:

```js
ComputeContacts    : Structure.Selections → InteractionData   // Mol* computes
CustomInteractions : Root, params.interactions → InteractionData   // YOUR list; computes nothing
InteractionsShape  : InteractionData → Shape.Provider          // the rendering
```

`InteractionsShape` consumes `InteractionData` **without knowing or caring where it
came from**. `ComputeContacts` and `CustomInteractions` are two alternative inlets
to the same object:

```ts
getCustomInteractionData(interactions: InteractionElementSchema[], structures): StructureInteractions
```

**So: compute with Buch, hand the pairs over, and Mol\* renders them with its
native visual.** Same for Luzar–Chandler, or any criterion we build tomorrow.
Mol\* never sees the criterion.

### The wire format is already our vocabulary

`InteractionElementSchema = { kind, a: StructureElement.Schema, b: StructureElement.Schema, description? }`,
and `StructureElement.SchemaItem` accepts **`atom_index`** directly (plus a
columnar form, `SchemaItems { items: { atom_index: [...] } }`).

MolSysMT yields atom-index pairs. **There is no vocabulary translation to write.**

```python
# Python → frontend
[{"kind": "hydrogen-bond", "a": {"atom_index": 3}, "b": {"atom_index": 7}}, ...]
```

### `kind` is styling, not semantics

Mol\*'s vocabulary is a closed set of ten: `hydrogen-bond`, `weak-hydrogen-bond`,
`ionic`, `pi-stacking`, `cation-pi`, `halogen-bond`, `hydrophobic`,
`metal-coordination`, `covalent`, `unknown`.

That does **not** constrain us. The criterion, the cutoffs, the provenance and the
occupancy live in Python; `kind` only tells Mol\* what colour to paint the line.
The criterion → `kind` projection is lossy **and it does not matter**, because the
scientific content never travels that way. `unknown` is the escape hatch for a
criterion with no native counterpart.

### The assumption that must be verified in a real browser, not assumed

**Mol\*'s `atom_index` must coincide with our index in `_molsys`.** It should — the
loader builds the model in that order — but if it did not, every H-bond would be
drawn between the wrong atoms **and would look entirely plausible**. This is the
first test of the domain, and it belongs in the real-browser harness
(`js/tests/e2e/`), because no unit test can catch it.

## 5. Why it is a new domain and not a corner of an existing one

An interaction is **a derived relation between pairs of atoms, re-evaluated per
frame, produced by a parameterised criterion.** No existing domain has that shape:

| domain | recipe? | re-evaluated per frame? | yields |
|---|---|---|---|
| **region** | ✅ | ✅ | a set of **atoms** |
| **shape** | ❌ (explicit geometry) | ❌ | drawn primitives |
| **measurement** | ❌ (endpoints chosen by hand) | value only | a **scalar** |
| **interaction** | ✅ | ✅ | a set of **edges** |

> **Interactions is to edges what Regions is to atoms** — Contract R applied to a
> graph instead of a set.

## 6. The unit is the **set**, not the edge

**The decision that makes or breaks the panel.** A solvated system has thousands of
hydrogen bonds. The domain's object is an **`InteractionSet`** — one recipe:

> *"hydrogen bonds between the ligand and the pocket, Luzar–Chandler,
> (d ≤ 3.5 Å, α ≤ 30°), dynamic"*

The panel lists **sets**, exactly as the Regions panel lists regions and not atoms.
A panel that lists individual edges is unusable on day one. The edges are the
*result* of the recipe, cached per frame — the same relationship a region has with
its `atom_indices`.

## 7. What the panel is actually for: **occupancy**

The number a scientist wants from an interaction over a trajectory is not "is it
there right now". It is **how much of the trajectory it survives**. Since the set
is re-evaluated per frame, this comes almost free:

- per set: interactions per frame — a curve;
- per edge: the fraction of frames in which it exists — the **occupancy**, the
  standard published metric for an H-bond in MD.

This is genuinely new scientific capability, not a re-skin of `add_hbonds` — and it
is reachable **only** because the interaction is a recipe rather than a drawing.

## 8. Rendering: native first, primitives left open (Contract V)

Per Contract V (`scene_objects_contracts.md`), an `InteractionSet` **owns** its
visual realisation rather than *being* it. So the realisation is **selectable**:

- **`renderer="native"` — the default, and the only one in the first slice.**
  `CustomInteractions` + `InteractionsShape`. Free, fast (instanced cylinders —
  which matters at thousands of edges), with picking and a colour theme per kind.
  The control it gives is exactly three knobs per kind: **`color`, `style`
  (solid/dashed), `radius`**. That is all Mol\* exposes.
- **`renderer="primitives"` — declared, not built.** The set materialises as a
  layer of **owned** shapes + annotations: total control (per-edge colour by
  occupancy, a label with the distance on every bond, a sphere at each midpoint),
  at the cost of reimplementing billboard label placement, dashes and picking, and
  of paying for thousands of individual shapes.

Build the second one when a real user needs it — **not before**. Two renderers are
twice the maintenance and twice the bugs. What matters is that the architecture
does not shut the door, and owning-the-realisation is what keeps it open.

## 9. Sketch of the API (to be refined, not settled here)

Inherits the canonical manager surface (S0) and identity (T):

```python
view.interactions.add(
    kind="hbond",                     # hbond | disulfide | salt_bridge | pi_stacking | ...
    selection_a="molecule_type==protein",
    selection_b="molecule_type==small_molecule",
    criterion="luzar_chandler",       # ← the provenance: named, never implicit
    cutoffs={"distance": "3.5 angstroms", "angle": "30 degrees"},
    mode="dynamic",                   # static | dynamic — as regions
    tag="site_hbonds",
)
view.interactions.occupancy(tag)      # per-edge fraction of frames
view.interactions.count_series(tag)   # interactions per frame
```

**Disulfide bridges are the odd one out**: covalent, part of the topology, not a
re-evaluable non-covalent contact. They fit as a `static` kind — say so explicitly
rather than letting the asymmetry pass unnoticed.

## 10. Scope is set by what MolSysMT can already compute

Measured 2026-07-12:

| kind | MolSysMT today |
|---|---|
| hydrogen bond | ✅ `hbonds/get_buch_hbonds.py`, `get_luzard_chandler_hbonds.py` (**two criteria**) |
| disulfide bridge | ✅ `build/get_disulfide_bonds.py` |
| contacts / neighbours / distances | ✅ `structure/get_contacts.py`, `get_neighbors.py`, `get_distances.py` (substrate for the rest) |
| salt bridge | ❌ |
| π-stacking | ❌ |
| hydrophobic contact | ❌ (`hydrophobic` appears only in `physchem/get_transmembrane_tendency.py` — a hydrophobicity scale, not an interaction) |
| halogen bond | ❌ |

**First slice: hydrogen bonds and disulfide bridges** — the two the ecosystem can
already compute, and the two most asked for. The rest is work **in MolSysMT**,
which is where an interaction criterion belongs. It must not be improvised inside
the viewer, or the viewer becomes a place where science hides.

## 11. Costs and traps

- **Per-frame cost.** Computing H-bonds every frame in Python is expensive. Needs
  the evaluation policy and cache that dynamic regions already have, and it must be
  **measured** (the ~3-second-per-message toll of the rework is the cautionary
  tale). MolSysMT has Taichi acceleration (`get_contacts_taichi`), so this is
  tractable, not free.
- **Scale.** Thousands of edges on a solvated system. The recipe must be
  selection-scoped, and "all H-bonds in the box" is a plausible request that will
  hurt.
- **The `atom_index` assumption** (§4) — verify in a real browser.

## 12. Core or add-on?

**Core.** Hydrogen bonds, disulfides and stacking are universal in molecular
visualisation — PyMOL, ChimeraX and Mol\* all ship them. This is not a specialty
like ElasNetMT; it is table stakes.

## 13. What this validates

A new domain drops into the architecture the scene-objects block establishes
**without bending anything**: a `TagsManager` (T), a manager with `.add()` (S0), an
authoritative summary (S1), serialisation of its **recipe** — not its edges — (S5),
undo (S6), and an owned visual realisation (V). That it fits without friction is
evidence the block's design is right.

Which is also why it must come **after** it.
