# Phase 0 — Migration guide (the breaking changes)

**Status:** proposed (2026-07-12). Companion to
[the spec](phase0_identity_and_managers.md) and
[the implementation plan](phase0_identity_and_managers_implementation_plan.md).

The subpanel phases add capability. **This one changes the public API**, and that is
what this third document exists for: the subpanels have a UI design where this has a
migration.

**Pre-1.0, breaking changes accepted** (decision, 2026-07-12). This is the moment they
are cheap. After 1.0 they are not.

---

## 1. The breaking changes

### 1a. `tags` becomes a method everywhere

| manager | today | after |
|---|---|---|
| `regions`, `shapes`, `measurements` | `tags()` — method | unchanged |
| **`annotations`, `selections`** | **`tags` — property** | **`tags()` — method** |

Today `view.annotations.tags()` raises `TypeError: 'list' object is not callable`, and
`view.measurements.tags` returns a bound method that looks like a truthy object. It is
a trap discovered only by walking into it.

```python
view.annotations.tags        # ❌ was: a list
view.annotations.tags()      # ✅ now:  a list
```

### 1b. `view.new_layer()` → `view.layers.add()`

The last survivor of the pre-Phase-13 style. `view.new_region()` →
`view.regions.add()` was migrated in that phase for exactly this reason; this one was
missed because `layers` had no manager to migrate *to*.

```python
view.new_layer(tag="pockets", kind="shapes")   # ❌ deprecated, then removed
view.layers.add("pockets")                     # ✅
```

### 1b-bis. `add_gaussian_isosurface` → `add_scalar_isosurface`

A literal alias (`pocket_blobs.py:142`): same function, same op, same signature.
`add_scalar_isosurface` survives — it names the wire op, it is the only one with a
test, and it describes *what* is produced rather than *how*.

```python
view.shapes.add_gaussian_isosurface(...)   # ❌ removed
view.shapes.add_scalar_isosurface(...)     # ✅
```

The internal `GroupLayer = Layer` alias (`layers.py:1194`) goes too — it is not
public, so it breaks nothing, but it makes the code talk about two things that are
one.

### 1c. A tag no longer identifies an object on its own

Not a signature change, but a **semantic** one, and the one most likely to surprise:

- `view.regions.add(tag='x')` now **succeeds** where a shape `x` exists (it already
  did — there was no guard — but now it is *intentional and safe*).
- A shape `x` and an annotation `x` can now **coexist** (today the shared
  `_scene_objects` guard forbids it).
- Any downstream code that assumed "a tag names one thing in the scene" must qualify by
  domain.

## 2. The corpus and the test suite, measured

Counted 2026-07-12 in `docs/`:

| change | files affected | example hits |
|---|---|---|
| `view.new_layer(...)` | **5** | `user/scene_management/layers.md:15`, `developer/regions_layers.md:15` |
| `annotations.tags` / `selections.tags` | **7** | `user/overlays/labels.md:106`, `developer/public_api.md:212` |
| `add_gaussian_isosurface` | **8** | listed alongside `add_scalar_isosurface` |

And in `tests/` — **the suite breaks, and that is expected, not a surprise**:

| | count |
|---|---|
| tests using `.tags` as a property | **8** |
| tests using `view.new_layer(...)` | **3** |
| tests asserting a tag collision is refused | **5** ⚠ |

**The five collision tests are the interesting ones.** They assert the *old* rule —
that a tag cannot be reused. Under Contract T some of those refusals become **legal**
(a region and a shape may share a tag), so those tests do not merely need editing:
each one must be **read and re-decided**. A test that is "fixed" by loosening its
assertion until it passes is a test that has been deleted with extra steps.

Small and tractable — but **the corpus is migrated in this same phase**, not "later".
Phase 13 of the rework exists precisely because documentation drifted from the API and
nobody noticed until a static resolver was written to find the dead calls.

### ⚠ `sandbox/Curso/` is hit, and **only the maintainer may fix it**

`sandbox/` is the maintainer's area and is **never touched** by the collaborator or by an
agent. But the `tags` change **does reach it**, and pretending otherwise would leave the
course quietly broken.

Located by a read-only grep (2026-07-12) — **two cells, both a `print`**:

```
sandbox/Curso/Unit_07.ipynb:61   print("Saved selections:",  view.selections.tags)
sandbox/Curso/Unit_14.ipynb:61   print("Active annotations:", view.annotations.tags)
```

After Phase 0 these do not raise — they print **`<bound method ...>`** instead of the
list, which is worse than an error: the cell still "works" and the course quietly teaches
nonsense.

**Action for the maintainer** (not for this phase's implementer): change both to
`.tags()`. One character each. It is listed here so it is a **handoff, not an oversight**.

### Two files that are *not* migrated

`docs/content/developer/architecture_snapshot_2025_11.md` and
`architecture_snapshot_2026_01.md` are **historical snapshots**. They describe what the
API was at a date. Rewriting them would be falsifying the record. **Leave them**, and
if it is not obvious that they are frozen, say so at the top of each.

Knowing the difference between a document that is *wrong* and one that is *historical*
is the whole reason this section exists.

## 3. The static resolver — **it must first be committed to the repo**

The rework built a **static API resolver**: a script that parses the code fences of
every `.md`, the code cells of every `.ipynb` and every `.py`, resolves each
`view.*` / `viewer.*` attribute chain against the live API, and reports what does not
exist.

**It is the only check that catches a dead call in a `.md` file** — executing the
notebooks cannot, because prose and fenced examples are never run. It is what found
`view.player.set_frame_range()`, a method the documentation had **invented** and that
never existed.

**⚠ It is not in the repository.** Verified 2026-07-12: `scripts/` contains only
`bootstrap.sh`, `dev.sh` and `validate_resources.py`. The resolver was written during
the rework and **was never committed** — it died with the session that made it.

So the first task of this phase is to **rebuild it and commit it**, at
`scripts/api_resolver.py`:

- it takes the corpus (`docs/`, and optionally `devguide/`) and the live `MolSysView`
  API;
- it reports every attribute chain that does not resolve;
- **it runs in CI**, so the corpus cannot drift from the API again without the build
  saying so.

A tool that only exists inside one session is not a tool; it is a thing that happened
once. This phase makes four breaking changes to the public API — it is exactly the phase
that needs the resolver to be a permanent, executable check rather than a memory.

**Acceptance gate of this phase: `scripts/api_resolver.py` is committed, wired into CI,
and reports zero unresolved calls across the corpus.**

## 4. What `architecture.md` must say afterwards

**§Key invariants 1 currently lies**, and after this phase it will lie more loudly:

> *"Tag uniqueness is global. A tag can appear in `_scene_objects` OR in `_layers`,
> never both."*

Both halves are false. It is false **today** (creating a shape `x` registers `x` in
`_scene_objects` **and** in `_layers`, as its degenerate auto-layer), and it becomes
false **by design** after Contract T.

Rewrite it to state the real rule: **identity is `(domain, tag)`; a tag is unique
within its domain; each domain owns a `TagsManager`.** Leaving the old text is worse
than having no text — a devguide that confidently states the opposite of the code is
how the next developer gets misled.

## 5. Deprecation policy for this phase

- `view.new_layer()` → **deprecate with a warning, migrate `docs/`, then remove within
  the phase.** There are no external users; carrying it costs more than it saves.
- `tags` property → **no deprecation shim is possible** (a property cannot warn *and*
  stay callable). It changes outright. This is the one that must be loudly stated in
  the changelog.

## 6. Acceptance

- `docs/` migrated; the static resolver reports **zero** unresolved calls.
- `architecture.md` §Key invariants 1 rewritten.
- The historical snapshots left intact, and marked as historical.
- The changelog names both breaking changes explicitly, in the user's words, with the
  before/after — not "improved tag handling".
