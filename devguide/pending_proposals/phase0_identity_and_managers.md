# Phase 0 — Identity and API coherence (spec)

**Status:** proposed (2026-07-12). One of three: this **spec**, the
[implementation plan](phase0_identity_and_managers_implementation_plan.md) (the seam,
site by site) and the [migration guide](phase0_identity_and_managers_migration.md)
(the breaking changes).

**Normative:** [`scene_objects_contracts.md`](scene_objects_contracts.md) — Contracts
**T** (identity) and **S0** (managers).

> The four subpanels each got three documents. **This phase is bigger than any of
> them, more dangerous than all of them, and it is the only one that cannot be done
> later.** It gets three too.

---

## 1. Why this phase exists

Two problems, and they turn out to be the same wound.

**The scene has no coherent notion of identity.** There are **four tag registries**
(`_regions`, `_scene_objects`, `_layers`, `_selections`), **three guards** (and
`_regions` has none), and **six counters** — with no shared rule. So
`view.regions.add(tag='x')` succeeds while a shape `x` exists, but a shape `x` and an
annotation `x` cannot coexist. There is no principle behind that line; it is where it
is by accident.

**The five managers drifted apart as they grew.** `tags` is a *property* in two and a
*method* in three (`view.annotations.tags()` raises `TypeError`). `shapes` is missing
six methods the others have — including `hide()`.

And that last gap is not cosmetic. **It is almost certainly why the Shapes panel
bypassed Python and repainted Mol\* directly** (§0.2): the API did not offer it the
same moves it offered annotations and measurements. Fix the API and the architectural
defect loses its excuse.

## 2. What lands

### 2a. Identity is `(domain, tag)` (Contract T)

A tag is unique **within its domain**. `site1` may be, at once, the region that
defines a binding site, the shape that marks it, the measurement that quantifies it
and the annotation that labels it — which is how the science reads.

- **A guard per domain** (five, plus `selection`), replacing the two asymmetric ones.
  `regions` gains the guard it never had.
- **The wire types its addressing**: `hide_layer`, `show_layer`, `delete_layer`,
  `set_layer_tag` carry the `kind`; `tagIndex` is keyed by `(kind, tag)`.
- **`_scene_objects` and `Layer.members` get qualified** — both are flat dicts keyed
  by bare tag, shared across domains that may now collide.

**The kind already exists on both sides.** Python: `SceneObject.kind`. Runtime:
`layerMeta` and `registerTaggedRef(ref, tag, kind)`. The runtime is *already told* the
kind of every ref and simply does not index by it. **Use it; do not invent it.**

### 2b. A `TagsManager` per domain (Contract T)

The tag policy of a domain becomes an object instead of a scattering across six
counters, three guards and five `_next_*_tag()` helpers.

Each owns: the prefix, the counter, the domain's uniqueness guard, and — the reason
the class earns its place — **the high-water mark, serialised with the session**.
Today the counters reset to zero on reload and the next auto-generated `measurement1`
collides with the imported one (§0.9). Only `regions` was ever fixed, and the fix was
never generalised. A `TagsManager` is where that lesson lives **once** instead of
being forgotten five times.

**It must not keep its own list of live tags.** That would be a second source of truth
about what exists, and it *will* drift from the registry — the exact sin Contract S1
forbids. It owns the **naming policy** and **asks** the registry what exists.

### 2c. The managers become one shape (Contract S0)

- **`LayersManager` is new.** Layers is the only domain with **no manager at all**
  (`view.layers` returns the raw registry), which is why its creation verb had to hang
  off the view itself. Copy the `RegionsManager` mould — **a `dict` subclass** — so
  `view.layers['x']`, iteration and `len()` keep working untouched.
- **`view.new_layer()` is retired** in favour of `view.layers.add()` — the house verb.
  It is the last survivor of the pre-Phase-13 style that `view.new_region()` →
  `view.regions.add()` already left behind.

  **Retiring it must not lose what it carried.** `new_layer(*, tag, kind, **meta)`
  accepts a `kind` and arbitrary `meta`, and `Layer.meta` is read in **14 places**. A
  bare `layers.add(tag)` would be a **feature regression**. The signature is:

  ```python
  view.layers.add(tag, *, kind=None, meta=None)
  ```

  **Explicit `meta=None`, never `**meta`.** A `**kwargs` bag silently swallows typos —
  `layers.add('x', kidn='shape')` would quietly become `meta={'kidn': 'shape'}` and the
  `kind` would never be set. That is precisely the class of silent failure this whole
  block exists to remove; we are not going to introduce a fresh one in its first phase.

  (Contract S0 asks for the same *verb* and the same *canonical surface*, not for
  identical signatures. `regions.add` has no `meta` because regions have no use for one;
  layers do.)
- **`tags` becomes a method everywhere.** Breaking change, accepted (pre-1.0).
- **`shapes` gains its six missing methods**: `count`, `records`, `delete`, `set_tag`,
  `show`, `hide`.
- **`annotations` gains a style mutator.** Verified 2026-07-12: there is **no
  `set_style`** — `label_style` is settable only at creation, and `info()` does not
  even report it. Without the mutator the Annotations panel would have to *recreate*
  an annotation to restyle it, losing its tag, its layer and its history. Add the
  mutator; do not let a panel recreate objects.
- **The undeclared aliases die** (§2d).
- **`selections.add()` cannot be called with its own defaults.** Verified 2026-07-12:
  the signature says `items: list[dict] | None = None`, but the ArgDigest validator
  **rejects `None`** — so `view.selections.add('x', atom_indices=[...])` raises
  `ArgumentError: due to the items argument with value None`. The caller must pass
  `items=[]` explicitly, which no reader of the signature would guess. **A default that
  the validator refuses is a broken default.** Fix the digestor (accept `None` → `[]`),
  not the signature.

### 2d. An undeclared alias is two names for one thing

Three aliases exist. One of them is fine, and the difference is the rule:

| alias | verdict |
|---|---|
| `add_gaussian_isosurface = add_scalar_isosurface` (`pocket_blobs.py:142`) | **public, undeclared → remove** |
| `GroupLayer = Layer` (`layers.py:1194`) | **internal, undeclared → remove** |
| `AddonWorkbenchSectionSpec = AddonSectionSpec` (`addons.py:276`) | ✅ carries `# Deprecated alias for backward compatibility` — **legitimate** |

**A declared deprecation is a temporary courtesy with an expiry date. An undeclared
alias is just two names for one thing** — it doubles the public surface, adds no
capability, and leaves neither name looking canonical. The docs must then pick one and
the other becomes a trap; a panel summary must map two names onto one op.

- **`add_gaussian_isosurface` goes; `add_scalar_isosurface` stays.** It is the name of
  the wire op (`op="add_scalar_isosurface"`), the only one with a test, and it names
  *what is produced* (an isosurface of a scalar field — the signature takes `values`)
  rather than *how* (a sum of gaussians), which is an implementation detail that may
  change.
- **`GroupLayer` goes.** It is more insidious for being internal: it makes the code
  talk about two things that are one, and `isinstance(x, GroupLayer)` in
  `scene_registry.py` reads as though a distinct "group layer" type existed. It does
  not. (It misled the author of these documents, before he went and looked.)

## 3. The risk, named

**Silent aliasing during a half-done migration.** Any site left indexing by a bare tag
will merge two objects with **no error and no trace**: hide the sphere `site1` and the
annotation `site1` vanishes with it.

This is the whole danger of the phase, and it is not theoretical — the codebase is
*full* of bare-tag indexing (`tagIndex`, `layerMeta`, `_scene_objects`,
`_tag_from_message`, the history rewriters). The [implementation
plan](phase0_identity_and_managers_implementation_plan.md) enumerates every one of
them, because a list is the only defence.

**The mandatory mutation test:** create the same tag in two domains, mutate one,
**assert the other does not move** — and confirm the test **fails** when `kind` is
dropped from the index key. If it still passes, the test is hollow and proves nothing.

## 4. Scope

**In:** identity, the `TagsManager`s, the manager surface, and the corpus migration the
breaking changes force (`docs/`).

**Out:**

- The panels. This phase changes **no GUI**. That is deliberate: it must be verifiable
  on its own.
- `Section` and `selection` panels — the domains gain their guards and managers, but
  their GUIs are not in this block.
- Anything in Phases 1–9.

## 5. What "done" means

- The canonical-surface table of Contract S0 is **fully green**, asserted by an
  introspection test — so the *next* manager cannot drift back out.
- A region and a shape can share a tag, and **operating on one does not touch the
  other** (mutation-verified).
- `view.layers.add('x')` exists; `view.new_layer` is gone; `docs/` is migrated.
- Auto-generated tags **do not collide after a reload** (the high-water marks
  serialise).
- **`architecture.md` §Key invariants 1 is rewritten.** It currently asserts a global
  tag uniqueness that the code does not have and, after this phase, deliberately will
  not have. Leaving it would make the devguide lie.
