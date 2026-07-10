# The `handleMessage` toll: a per-message, O(system-size) performance bug

**Status:** diagnosed 2026-07-10, **not fixed**. Highest-impact defect found in the
Regions/Whole audit. Independent of every contract; fix it first.

**Summary:** every message the viewer receives from Python — *including messages whose `op`
is unknown and which do nothing* — rebuilds the entire visible Studio panel, whose group
strip holds one DOM node per residue. On a 95,000-atom system this costs **3.1 seconds per
message**, on a 20-core workstation, with the rasteriser paused.

---

## 1. Measurements

Chromium (`/usr/bin/google-chrome`) via Playwright, headless, ANGLE + SwiftShader.
`canvas3d.pause(true)` so no rendering is measured. Synthetic poly-ALA systems (5 atoms per
residue). Median of 5 runs. **Machine: 20-core workstation** — DOM construction is
single-threaded, so cores do not help; a laptop will be slower.

### 1.1 The toll is independent of the message

| op | n = 95,000 atoms |
|---|---:|
| `__does_not_exist__` (falls through to `default:`, only a `console.warn`) | **3,183 ms** |
| `hide_region` | 3,159 ms |
| `show_region` | 3,191 ms |
| Mol\* empty state-tree update, for scale | **0.4 ms** |

Hiding a region costs exactly what an unknown message costs. Mol\* is not involved.

### 1.2 The toll is the panel rebuild, and it is paid twice

| call | n = 2,000 | n = 20,000 | n = 95,000 |
|---|---:|---:|---:|
| `applyWorkbenchMessage` | 0 ms | 0 ms | 0 ms |
| `refreshNavigatePanel` | 48 ms | 328 ms | **1,617 ms** |
| `refreshAddonsPanel` | 45 ms | 317 ms | **1,596 ms** |
| `syncStripOverlaysForMessage` | 0 ms | 0 ms | 0 ms |
| **`handleMessage` total** | 90 ms | 666 ms | **3,133 ms** |

Linear in system size. **No regions, annotations or saved selections existed during this
measurement.**

### 1.3 Where it actually goes

| call | n = 95,000 |
|---|---:|
| `groupPanel.setAnnotations([])` | 0 ms |
| `groupPanel.setSavedSelections([])` | 0 ms |
| `groupPanel.setRegions([])` | 0 ms |
| `groupPanel.setRuntimeVisible(null)` | **1,647 ms** |
| `groupPanel.render()` | **1,604 ms** |
| group-strip DOM nodes present | **19,000** |
| active tab | `system` |

The first three cost **zero**: `BasePanel`'s render-on-show works exactly as designed, and
hidden panels do not paint. The cost is one call — `render()`.

---

## 2. Root cause

`js/src/managers/viewer-controller.ts`, at the end of `handleMessage`, **outside** the
`switch`, after every message including the `default:` branch:

```ts
            this.applyWorkbenchMessage(msg);
            this.refreshNavigatePanel();
            this.refreshAddonsPanel();
            this.syncStripOverlaysForMessage(msg);
```

- `refreshNavigatePanel()` ends with `this.refreshPanelWorkspaceChrome();`
- `refreshAddonsPanel()` **also** ends with `this.refreshPanelWorkspaceChrome();`

`refreshPanelWorkspaceChrome()` calls `this.groupPanel.setRuntimeVisible(null)`, and in
`js/src/ui/group-panel.ts:574-577`:

```ts
    setRuntimeVisible(visible: boolean | null): void {
        this.runtimeVisibleOverride = visible;
        this.render();               // ← no comparison with the previous value
    }

    render(): void {
        this.systemPanel.rebuild();  // ← full teardown of the group strip
    }
```

`SystemPanel.rebuild()` reconstructs one DOM node per residue. Two chrome refreshes per
message × 1.6 s = the 3.13 s measured.

In steady state `runtimeVisibleOverride` is **always `null`**, so both rebuilds are
guaranteed no-ops in effect and pure cost in fact.

---

## 2b. A second, independent defect: every region is built twice

`molsysviewer/viewer/regions.py`, in `new_region`:

```python
region._send_create()
if representation is not None or repr_params:
    region.set_representation(representation, skip_digestion=True, **repr_params)
```

`_send_create()` emits `create_region` **carrying the representation and params**, and the JS
handler builds the Mol\* component *and adds the representation*. The very next statement emits
`set_region_representation`, whose handler begins
(`js/src/managers/handlers/state-handlers.ts:452`):

```ts
await this.removeStateObject(entry.component);
```

It **tears down the component that was just created and rebuilds it from scratch.**

Every region created with a representation pays for two full component builds:
`new_view(selection=…)`, `styles.focus()`, `make_regions_by(representation=…)`, every
`→ Region` promotion, and every region restored on rebuild
(`_rebuild_view_from_current_molsys` does `_send_create()` then `set_representation()` too).

**Fix:** `new_region` must not double-send. Either `_send_create()` carries the full visual spec
and no `set_representation` follows, or `_send_create()` carries no visual and
`set_representation` is the only builder. The second is cleaner and aligns with Contract A
(`region_contracts.md`), where a region may legitimately have **no** representation: create the
component bare, then apply a visual only if one was requested.

This also inflates the Decision 2 benchmark (`scene_master_plan.md` Phase 1): the measured cost
of "building the whole's complement component" includes a redundant build-and-teardown.

---

## 3. Why it was never noticed

- **No performance test exists.** Not one. Nothing in `npm run test:js` or the Python suite
  measures time.
- The unit tests use 4-atom PDBs, where the toll is sub-millisecond.
- The Python-side **batch context** (`_batch_updating`, collapsing `show_all`/`hide_all`/
  `make_regions_by` into a single summary) was designed as an anti-flicker optimisation. It is
  in fact a workaround for this toll, applied without knowing the toll existed. It hides the
  symptom for three operations and leaves every other message paying full price.
- Every message pays it: one per frame during trajectory playback, one per chain during
  `make_regions_by`, one per region during any un-batched loop.

---

## 4. The fix, in four layers

Ordered surgical → structural. Layers 1–2 recover almost all of the cost; 3–4 are the correct
architecture.

**Layer 1 — idempotent setter.** `setRuntimeVisible` returns early when the value is
unchanged:

```ts
    setRuntimeVisible(visible: boolean | null): void {
        if (this.runtimeVisibleOverride === visible) return;
        this.runtimeVisibleOverride = visible;
        this.render();
    }
```

**Layer 2 — call the chrome refresh once.** `refreshNavigatePanel()` and
`refreshAddonsPanel()` must not each invoke `refreshPanelWorkspaceChrome()`. Hoist it to the
single caller in `handleMessage`, or make it idempotent-and-cheap.

**Layer 3 — targeted updates.** `handleMessage` must not refresh both panels after *every*
message. A message updates what it concerns. This is the same defect class we removed from the
query panels (full repaint per keystroke), one level up: full panel refresh per message.
Concretely: build a map from `op` → the refreshes that op actually requires, and default to
none.

**Layer 4 — the strip does not scale.** 19,000 live DOM nodes is heavy even when nothing
rebuilds them: memory, layout, and every `querySelectorAll` in the codebase. `SystemPanel`
needs either incremental reconciliation (diff, not teardown) or virtualisation (render only
the rows in view). This is required for the viewer to be usable on ribosome-scale systems at
all, independent of the toll.

---

## 5. Acceptance criteria

- A message with an unknown `op` costs **< 5 ms** at n = 95,000 (today: 3,183 ms).
- `hide_region` / `show_region` cost **< 20 ms** at n = 95,000 (today: ~3,170 ms).
- `handleMessage` for a message that changes nothing performs **zero** `systemPanel.rebuild()`
  calls. Assert on a spy, not on a timer.
- `new_region(representation="cartoon")` performs **exactly one** `StructureComponent` commit.
  Assert on a spy (§2b).
- Group-strip DOM node count stays bounded (Layer 4) or is explicitly documented as O(residues)
  with a measured ceiling.

### 5.1 Performance budgets (the harness enforces all of them)

A budget suite that watches only `handleMessage` will let the next regression through somewhere
else. Every budget is measured at n = 95,000 atoms, rasteriser paused, and recorded with the
machine identity. Numbers are ceilings to be set from the first clean run, not guesses.

| Operation | Budget | Today |
|---|---|---|
| unknown `op` | < 5 ms | 3,183 ms |
| `hide_region` / `show_region` | < 20 ms | ~3,170 ms |
| `create_region` with a representation | one component commit | **two** (§2b) |
| `load_structure_from_string` | record + ceiling | 9,248 ms |
| per-atom colour write (`set_atom_colors`) | record + ceiling | not measured |
| one trajectory frame advance | < 16 ms (60 fps) | not measured |
| one frame advance with a `dynamic` region | budgeted separately | n/a |

The trajectory budgets matter beyond this fix: Contract R's dynamic regions
(`region_contracts.md`) re-evaluate on frame change and emit one consolidated message per frame.
**That design is only viable once this toll is gone**, which makes Phase 0 a hard prerequisite
of Decision 1, not merely a performance improvement.

---

## 6. The performance harness

The measurements above were produced with an ad-hoc Playwright script. **It must land in the
repository** as a permanent test, because the absence of one is precisely why a three-second
regression shipped:

- Location: `molsysviewer/js/tests/perf/message-toll.perf.ts`, run by a new
  `npm run test:perf`.
- Launch flags that matter: `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`.
  With `--use-gl=swiftshader` alone, Mol\* fails with *"Could not create a WebGL rendering
  context"* and the harness silently degrades.
- Pause the rasteriser (`plugin.canvas3d.pause(true)`) before timing, or SwiftShader's redraw
  dominates and hides everything.
- The structure accessor is
  `plugin.managers.structure.hierarchy.current.structures[0].cell.obj.data`; the controller's
  public method is **`getStructureData()`**.
- Assert on **budgets**, not on absolute times, and record the machine in the output.

---

## 7. Collateral finding: `getStructure()` does not exist

`getStructure` is the name of a *callback* in the handler callback interface
(`js/src/managers/handlers/state-handlers.ts:72`), which the controller satisfies with
`getStructure: () => this.getStructureData()` (`viewer-controller.ts:1262`). There is **no
`getStructure()` method on the controller**.

`js/tests/e2e/region-hide.e2e.ts` does:

```ts
const structure = (controller as any).getStructure?.();
const n = structure?.elementCount ?? 0;
const atomIndices = Array.from({ length: n }, (_, i) => i);
await controller.handleMessage({ op: "create_region", tag: "region1", atom_indices: atomIndices, ... });
await controller.handleMessage({ op: "hide_region", tag: "region1" });
```

`getStructure` is `undefined`, so `n === 0`, so the region is created with an **empty index
array**; `createRegion` logs a warning and creates nothing; `hide_region` then hides nothing.
The test proceeds to assert on the context menu and passes green. **The e2e that gives the file
its name never exercises a hidden region.**

Three mechanisms conspired: a cast to `any` that disabled the compiler, an optional call `?.()`
that turned a programming error into silence, and an assertion aimed at something else.

Fix: call `controller.getStructureData()`, assert `n > 0`, and assert the region exists before
hiding it.
