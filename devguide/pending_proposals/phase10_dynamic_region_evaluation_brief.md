# Phase 10 — Dynamic-region evaluation · design brief

**Author:** backend contract owner · **For:** the collaborator implementing Phase 10
**Status:** ready to start **after** the Phase 9 frontend (Layers subpanel) lands.
**Size:** L · **Depends on:** P0, P5, P6 (all done) · **Implements decisions 1 + A + B4.**

This is a design brief, not an implementation. It fixes the architecture, the message
protocol and the contract points, and lists the work items with code pointers. You own the
implementation; I audit it by mutation testing at the end (see *§8*).

---

## 1. Goal

A **dynamic, `frame_dependent`** region must re-evaluate its recipe as the trajectory plays,
so *"waters within 5 Å of the ligand"* tracks the ligand frame by frame. A **topological**
dynamic region (e.g. `chain A`) must cost **zero** during playback. This is the behaviour half
of Contract R — the model (`mode`, `frame_dependent`, re-evaluable provenance) and the state
format already exist (Phases 5 and 6). You are adding **evaluation**.

**Acceptance (from the master plan):**
- *"waters within 5 Å of the ligand"* tracks a trajectory.
- A `chain A` dynamic region costs zero during playback.
- Playback with N dynamic regions emits **exactly one message per frame** (not one per region).

---

## 2. The architectural crux — read this first

Decision A says recipes are evaluated **in Python, lazily, one consolidated message per frame**.
But **frames advance in the frontend** (Mol\* trajectory playback), and today Python only hears
about a frame change **when playback stops**:

- `viewer-controller.ts:1373` → `onPlaybackStopped: (frame) => notify({event:"trajectory_frame_changed", frame})`.
- Python side: `core.py` `elif event == "trajectory_frame_changed"` — the comment literally says
  *"Emitted by TS when playback stops."*
- There **is** a per-frame hook in the frontend already — `this.trajectory.onTrajectoryState((state)=>…)`
  at `viewer-controller.ts:1389` fires on every `state.currentFrame` change — but it does **not**
  notify Python today.

So the resolution is a **pull model**:

```
 frontend frame display (onTrajectoryState, per frame)
        │  request_dynamic_region_evaluation { frame }      (JS → Python, lightweight, coalesced)
        ▼
 Python: evaluate frame_dependent∧dynamic∧active regions for `frame`,
         lazily, cached per (region_uid, frame)
        │  set_dynamic_region_atoms { frame, regions:[{tag, atom_indices}] }   (Python → JS, ONE message)
        ▼
 frontend applies the atom-index deltas to the region components
```

Notes that make or break this:
- **This is only viable because P0 removed the ~3 s-per-message toll.** One request + one response
  per displayed frame is now affordable. Do not fan out per region.
- **Coalesce.** During fast playback frames arrive faster than Python can evaluate. The frontend
  must send only the **latest** pending frame and drop stale requests; Python evaluates the frame
  it was asked for. Never queue a backlog.
- **The response is runtime-only.** `atom_indices` is a *cache* of the recipe result (Contract R),
  never authoritative state. Send it with `self._send_runtime_only(...)` so it never lands in
  `export_state`. A reload re-derives it.

---

## 3. Message protocol (two new messages)

**JS → Python** (add to the `_handle_frontend_event` event chain in `core.py`):

```jsonc
{ "event": "request_dynamic_region_evaluation", "frame": 42 }
```

**Python → JS** (runtime-only; add the op to `viewer-messages.ts` and a handler in the controller):

```jsonc
{
  "op": "set_dynamic_region_atoms",
  "frame": 42,
  "regions": [
    { "tag": "waters_near_ligand", "atom_indices": [/* the frame-42 set */] }
    // ONLY regions whose set CHANGED vs what is currently displayed; may be empty.
  ]
}
```

The `regions` array carries the **deltas of changed regions only** — if a frame-dependent region's
atom set for this frame equals what is already on screen, omit it. An empty array is a valid, common
message (the ligand did not move enough to change the 5 Å shell).

---

## 4. Backend work items (Python)

**4.1 — Thread `structure_index` through evaluation. (This is the central gap.)**
`RegionsMixin._evaluate_region_provenance(region)` (`viewer/regions.py:88`) evaluates a recipe but
has **no frame parameter** — its `msm.select(...)` call omits `structure_indices`, so a distance
selection silently uses frame 0. Add a `structure_index` argument and pass
`structure_indices=[structure_index]` into `msm.select` (and any coordinate-dependent `msm.get`).
Topological kinds (`split`, `boolean`, `complement`, `duplicate` over topological operands) ignore
it. This is the line that makes *"within 5 Å"* actually track.

**4.2 — Per-frame evaluation entry point.**
Add e.g. `RegionsMixin._evaluate_dynamic_regions_for_frame(frame) -> list[dict]`. It:
- selects the regions to evaluate: `region._active and region.mode == "dynamic" and region.frame_dependent`;
- for each, gets `atom_indices` from the **cache** (§4.3) or evaluates via §4.1 and caches;
- compares to the region's **currently displayed** set (the region's live `atom_indices`); if
  changed, updates `region._set_atom_indices(...)` and includes `{tag, atom_indices}` in the result;
- returns the consolidated list. The `trajectory_frame_changed`/request handler sends **one**
  `set_dynamic_region_atoms` with that list.

**4.3 — Cache, keyed `(region_uid, structure_index) → tuple[int, ...]`.**
Lazy fill on first display of a frame. Invalidation (each of these must drop the affected entries):
- **topology change / `apply_system_edit`** → clear the whole cache (indices reference a stale space);
- **recipe change or region delete** → drop that region's entries;
- a region leaving `dynamic` or `frame_dependent` → drop its entries.
Keep it bounded (a frame window or an LRU); document the bound. Do **not** serialise the cache.

**4.4 — Budget enforcement + freeze-to-static. "Never silently drop frames."**
Wrap the per-frame evaluation in a wall-clock budget. If a region's evaluation exceeds it:
- emit a warning through the smonitor/catalog path (not a bare `warnings.warn` — match how the
  codebase emits; see `_private/smonitor_emit`);
- **offer to freeze**: set the region back to `mode="static"` (it stops re-evaluating and keeps its
  last set) and surface that choice to the user (a runtime message the GUI can act on, or at least a
  logged, testable event). Playback continues at the current frame's result — frames are never
  dropped.

**4.5 — Topological dynamic regions re-evaluate on topology change only**, never per frame. They are
already excluded by the `frame_dependent` filter in §4.2; add a test that proves a `chain A` dynamic
region emits nothing during playback (the "costs zero" criterion).

---

## 5. Frontend work items (TypeScript)

**5.1 — Signal frame display to Python.** In the `onTrajectoryState` subscription
(`viewer-controller.ts:1389`), emit `request_dynamic_region_evaluation {frame}` — **coalesced**
(latest frame only; drop stale). Gate it: only send when at least one dynamic frame-dependent region
exists (Python can tell you via a flag on `set_region_summaries`, or track it from region summaries
you already receive). No regions → no traffic, so a plain trajectory stays silent.

**5.2 — Apply the consolidated deltas.** Handle `set_dynamic_region_atoms` in the controller
(`viewer-controller.ts` op switch) and update each region's Mol\* component atom set. Regions live in
`state-handlers.ts` as `regionIndex: Map<tag, {atomIndices, …}>` created via `createRegion`. You need
an **efficient atom-set update** for a component — swapping the whole component per frame at 30 fps
must not thrash. Measure it; if recreating the component is too slow, update the component's selection
in place.

**5.3 — Perf harness.** Add a *"frame advance with a dynamic region"* budget to the perf harness
(`tests/perf/…`, cf. `region-order-ownership.probe.ts`): advance N frames with a frame-dependent
region and assert the per-frame update stays under budget and emits exactly one message per frame.

---

## 6. Contract points that must hold (I will check these)

1. **Exactly one `set_dynamic_region_atoms` per displayed frame**, regardless of N regions.
2. A **topological** dynamic region emits **nothing** during playback.
3. The `structure_index` genuinely reaches `msm.select` — reverting §4.1 must make *"within 5 Å"*
   stop tracking (a frame-1 set differs from a frame-N set).
4. The cache is **not** serialised, and is invalidated on `apply_system_edit`.
5. Over-budget → the region **freezes to static** and playback continues; nothing is silently dropped.
6. `atom_indices` stays a runtime cache: `export_state` never carries a per-frame set.

---

## 7. Standing constraints (unchanged)

- Never hand-edit `molsysviewer/viewer.js`; rebuild with `npm run build:runtime`.
- Never commit `sandbox/Test.ipynb`; leave `devguide/course/` alone.
- Commit only when asked; push only when asked; work on `main`.
- No "Co-Authored-By" / Claude mentions in commit messages.
- **Green** = `pytest` + `npm run test:js` + `npm run build:runtime` + `npx tsc --noEmit` with no
  new errors (8 pre-existing). Add a browser E2E where it earns its keep.

## 8. What the audit will do (so build for it)

I verify by **mutation**: for every mechanism above I revert it and its test must fail. Please land
tests that pin, individually and mutation-provably:
- frame reaches `msm.select` (§4.1) — the tracking test;
- one-message-per-frame consolidation (§6.1);
- topological region silent during playback (§6.2);
- cache invalidation on `apply_system_edit` (§6.4);
- over-budget freeze-to-static (§6.5);
- `atom_indices` absent from `export_state` for a dynamic region (§6.6).

If any of these can't be pinned by a unit test, tell me — that usually means the mechanism needs a
seam, and it is cheaper to add the seam now than during the audit.
