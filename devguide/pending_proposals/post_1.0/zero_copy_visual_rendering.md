# Proposal: Large-System Rendering Performance (Binary Transport, In-Place Updates, and the Limits of Zero-Copy)

**Status:** design / planning (feasibility-grounded). Not implemented.
**Current transport proposal:** see
[`data_plane_architecture.md`](../../data_plane_architecture.md). This document
is the deeper post-1.0 feasibility analysis and must not be read as a second wire
protocol.
**Consolidates:** this document folds in and supersedes the former
`visual_scaling_zero_copy.md` (same problem space, viewed from the TopoMT
large-shape-set angle).
**Scope owner:** MolSysViewer (transport + frontend); some tiers are MolSysMT /
Mol\* upstream or out of scope (documented below).

## Abstract

Two earlier proposals ("Zero-Copy Visual Rendering" and "Visual Scaling and
Zero-Copy Rendering for Large Complexes") asked for a comprehensive zero-copy
GPU pipeline: in-place VBO updates (`gl.bufferSubData`), GPU-compute surfaces,
shader-based selection, vertex-shader frame interpolation, WebGPU shared storage
buffers, and `cl_khr_gl_sharing` between a Python solver and the browser.

A code-and-feasibility audit shows these conflate **three very different things**,
only the first of which is MolSysViewer's to solve and achievable now:

1. **Transport** (Python kernel → browser): optimizable at the MolSysViewer
   level. **Feasible, high value.**
2. **Geometry update in the browser**: bounded by Mol\* — most representation
   geometry (cartoon, molecular surface) is *derived* from coordinates and has
   no 1:1 coordinate→vertex mapping, so a raw `bufferSubData` position overwrite
   is not generally valid.
3. **Cross-process GPU sharing** (`cl_khr_gl_sharing`, WebGPU shared buffers
   between the Python process and the browser): **infeasible over the Jupyter
   comm channel**, where the kernel and the browser are separate processes
   (often separate machines).

This document reframes the work into **feasibility tiers** with an explicit
ownership and acceptance criterion for each.

**On necessity (read this before building anything).** The single most valuable
output of this proposal is the *document itself*: it prevents the impossible
tiers (3–4) from being re-derived as local work. Beyond that, **nothing here is
both necessary and easy pre-1.0.** The transport win is only a ~4–5× constant
factor on a one-time load, and no profile yet shows it hurting. An earlier draft
claimed shape-set batching was a demonstrated present pain — that was wrong: the
code **already batches** every shape set into one message (verified; see Audit),
so there is no low-hanging, presently-justified win to grab. Everything remaining
should wait for a **triggering benchmark** — a concrete system/trajectory that
measurably hurts — before any code is written. See "Prioritization" at the end.

---

## Audit: current reality (what the code actually does)

* **Trajectory load.** `view.load(...)` serializes *all* frames into the
  `load_molsys_payload` (coordinates as JSON arrays via
  `loaders/load_molsysmt.py`). The whole trajectory is loaded into Mol\* once and
  **animated client-side** (`set_trajectory_playback` / `playTrajectory` in
  `trajectory-handlers.ts`). So the "rebuild the mesh on every frame" failure
  mode described in the proposals does **not** occur for a loaded trajectory —
  Mol\* steps through preloaded models. The real cost here is the **initial
  payload size** (every frame's coordinates as text JSON).
* **Streaming / live coordinate edits.** `partial_coordinates_update`
  (`trajectory-handlers.ts`) mutates the Mol\* model's
  `atomicConformation.x/y/z` arrays **in place**, bumps the conformation id, and
  runs `state.updateTree(...)`. Mol\* then **re-derives** the representation
  geometry from the new coordinates. This is *not* a `bufferSubData` position
  overwrite — for cartoon/surface the geometry recompute is inherent (spline /
  marching cubes), and that recompute, not the upload, is the cost.
* **Transport.** Everything currently travels as **JSON** over the AnyWidget
  comm. **No binary buffers are used today**, although AnyWidget fully supports
  them (`widget.send(content, buffers=[...])` ↔ JS `model.on("msg:custom", (msg,
  buffers) => ...)`).
* **Shapes.** Large shape sets are **already batched**: `add_tetrahedra`,
  `add_alpha_sphere_set`, `add_rings`, `add_triangle_faces`, `add_network_links`,
  etc. each send **one** message whose `options` carries the full arrays (e.g.
  `tetra_coords`, `atom_quads`, `colors`). The per-object Python loops only build
  those lists; there is **no** per-object message flood. So the residual cost is
  *not* message count — it is that the single batched message is **JSON** (text
  expansion of the numeric arrays inside it), i.e. the same transport issue as
  coordinates, not a distinct batching problem.

---

## Tier 1 — Binary transport + message batching (FEASIBLE, MolSysViewer-level)

**Correction (verified against the code).** An earlier draft split this into
"1a shape-batching (do now)" and "1b binary coordinates (later)" on the premise
that shape sets flood the channel with one message per object. **That premise is
false:** the shape ops already batch every set into a single message (see Audit).
So there is *no* separate, presently-justified batching win. What remains is a
single concern — the numeric payloads (coordinates *and* the arrays inside the
batched shape messages) travel as **JSON text** — and it is uniformly
**profile-gated**:

* **Binary + compressed numeric transport: do only once profiled.** A ~4–5×
  constant factor (more with compression, below) on a *one-time* load; real but
  speculative until a concrete large system measurably hurts. This covers both
  coordinate arrays and the arrays carried inside already-batched shape messages.
  Do not build ahead of that evidence.

### What this tier does and does *not* do
Tier 1 is **purely a transport optimization**. It reduces the *bytes on the wire*
and the *number of messages*; it does **not** change how Mol\* turns coordinates
into geometry. Once the binary coordinates arrive, the frontend still feeds them
through the existing `partial_coordinates_update` path (in-place mutation of
`atomicConformation.x/y/z` + `updateTree`), and Mol\* still re-derives
cartoon/surface geometry as it does today. Speeding up that *recompute* is Tier 2
(coordinate-level) and Tier 3 (engine-level), not Tier 1. Keeping this boundary
explicit prevents over-promising "zero-copy rendering" from a change that is
really "zero-copy *transport*."

### Approach
* Send coordinate arrays as binary **`Float32Array`** via AnyWidget `buffers`
  instead of JSON, for both:
  * the **initial trajectory payload** (the dominant cost for multi-frame loads),
  * `partial_coordinates_update` (streaming / live edits).
* **Batch** large shape sets into a single binary message (one payload for
  thousands of spheres/tetrahedra) rather than one message per object.
* Keep a JSON fallback for environments/messages where binary is unavailable.

### Wire format (binary buffers)
AnyWidget delivers `widget.send(content, buffers=[...])` to the frontend as
`model.on("msg:custom", (msg, buffers) => ...)`, where `buffers` is an ordered
list of `DataView`/`ArrayBuffer`. The JSON `content` carries only the **header**
(shape, dtype, units, and which buffer index holds what); the numbers travel in
the buffers. Proposed envelopes:

* **Coordinates** (initial payload and `partial_coordinates_update`):
  ```jsonc
  // content
  {
    "op": "load_molsys" | "partial_coordinates_update",
    "options": {
      "encoding": "binary-f32",        // absent  => legacy JSON arrays
      "n_frames": F, "n_atoms": N,
      "layout": "frame_major",         // flattened [F][N][3], C-order
      "coordinates_buffer": 0,         // index into `buffers`
      "units": "nm"                    // coords stay in MolSysMT's nm contract
    }
  }
  // buffers[0] = Float32Array of length F*N*3, x0,y0,z0,x1,y1,z1,...
  ```
  The frontend reads `buffers[options.coordinates_buffer]` as a `Float32Array`
  and slices per frame (`stride = N*3`). Endianness is little-endian (the only
  layout AnyWidget/Jupyter transmit; the decoder asserts it via a known marker
  rather than trusting the platform).
* **Batched shapes** (TopoMT tetrahedra/clouds):
  ```jsonc
  // content
  {
    "op": "add_shapes_batch",
    "options": {
      "encoding": "binary-f32",
      "kind": "sphere" | "tetrahedron" | ...,
      "count": M,
      "vertices_buffer": 0,            // geometry (e.g. centers, or vertex soup)
      "attributes": { "radius_buffer": 1, "color_buffer": 2 },
      "ids": [...]                     // stable ids stay in JSON for history/replay
    }
  }
  ```
  One message replaces M per-object messages; the per-shape *identity* (ids,
  semantic labels) stays in JSON so the reproducible history is unaffected
  (see Reproducibility constraint).

### Implementation sequencing
1. **Python send path** — add a `_send_binary(content, buffers)` helper alongside
   the existing `_send` / `_send_runtime_only` / `_send_replay` in `core.py`, so
   the binary path obeys the same record-vs-runtime discipline (the *header* may
   be recorded; the buffer is ephemeral). No new public API.
2. **Serialization** — in `loaders/load_molsysmt.py`, emit coordinates as a
   `float32` C-contiguous array + header instead of nested JSON lists when binary
   is enabled; gate behind a capability flag so the JSON path remains the default
   fallback.
3. **Frontend decode** — in the message handlers (`trajectory-handlers.ts` for
   coordinates, the shapes handler for batches), branch on
   `options.encoding === "binary-f32"`: read from `buffers[...]`, otherwise take
   the legacy JSON arrays. The geometry-application code downstream is unchanged.
4. **Shape batching** — add the `add_shapes_batch` op end to end (message type in
   `viewer-messages.ts`, Python emitter, TS handler that constructs the Mol\*
   shape group once).
5. **Capability negotiation / fallback** — detect binary support once at
   handshake (or feature-flag it) and fall back to JSON transparently; the public
   behaviour and the exported/replayed format must be identical either way.

### Compression — where the real win is (beyond raw f32)
Plain `float32` is only ~4–5× smaller than JSON. The domain-specific wins are
larger and already-proven, and should be considered part of 1b rather than a
separate initiative:

* **Integer quantization.** Encode coordinates as 16-bit fixed point relative to
  a per-frame (or per-model) bounding box → another ~2× over f32, at a precision
  loss that is invisible for rendering.
* **Inter-frame delta encoding.** Trajectory coordinates change little between
  consecutive frames; delta + integer packing is where the *order-of-magnitude*
  gains for long trajectories live.
* **Reuse the proven strategy.** This is exactly what **BinaryCIF** does (column
  encodings: delta, run-length, integer packing) — and **Mol\* already decodes
  BinaryCIF natively**. We should reuse its *encoding strategy* (and, if the shoe
  fits, its decoder) rather than inventing a bespoke float buffer format. This
  reframes 1b: the point is not "f32 instead of JSON," it is "a compact,
  Mol\*-aligned coordinate encoding."

### Reproducibility constraint
The **exported / replayed** format stays JSON-friendly and self-describing.
Binary buffers are a **live-session transport optimization**, not the export
format — mirroring the decision taken for the visibility-delta protocol (full
state stays reproducible; the optimized wire form is ephemeral).

### Ownership
MolSysViewer (`load_molsysmt.py` serialization + `widget.py` send path + the TS
loader/handlers + message decoders). Possibly a thin contract with MolSysMT to
expose read-only coordinate array views to avoid a CPU copy *on the Python side*
(a Python-side optimization, distinct from cross-process GPU sharing).

### Acceptance criteria
1. Loading an N-frame trajectory or thousands of shapes transmits bytes
   proportional to the **raw numeric data**, not to a text-JSON expansion of it.
2. The comm channel is not flooded by per-object messages for large shape sets.
3. Export/replay remains JSON and reproducible (no dependence on the binary
   transport).

### Relations
Same traffic-reduction family as [[jupyter_websocket_redundancy_overflow]] and
the already-implemented versioned visibility-delta protocol.

---

## Tier 2 — Coordinate-level frame interpolation (FEASIBLE with effort, Mol\*-aware)

### Approach
Let Python stream sparse frames (5–10 fps) and have the client **interpolate
coordinates (CPU LERP between frame K and K+1)** and apply them through the
existing in-place path, masking network jitter. This achieves most of the
proposals' "buttery 60 fps from a slow stream" goal **without** the vertex-shader
LERP (which would require forking Mol\*).

### Caveat to document
Cheap per-frame updates only hold for representations with a near 1:1
coordinate→vertex mapping (spacefill/points). Cartoon and molecular-surface
representations re-derive geometry from coordinates, so per-frame updates remain
recompute-bound regardless of transport. The plan should document a recommended
representation for large dynamic systems.

### Topological signature guard (safety precondition)
Any in-place coordinate update — whether from interpolation or a streamed frame —
must first assert that the incoming array's **topological signature** matches the
loaded model: same atom count and same per-frame `N*3` stride as the active
`atomicConformation`. A mismatch means atoms were added/removed/reordered, which
is a *topology change*, not a coordinate update, and must take the full reload
path instead of the in-place mutation. This guard belongs in the frontend decode
step (Tier 1, step 3) and protects both Tier 1 streaming and Tier 2
interpolation from silently writing misaligned positions.

### The load-upfront memory ceiling (why transport alone is not enough)
Binary transport (Tier 1) shrinks the *transfer*, but the current design loads
**all frames into Mol\* at once** and animates client-side — so `N_frames ×
N_atoms` coordinates all live in browser (and GPU) memory simultaneously. No
encoding fixes that: it is a *memory* ceiling, not a *bandwidth* one. For truly
large trajectories the answer is **streaming a sliding window** of frames
(load/evict around the playhead) — which is this tier's job, not Tier 1's. State
this limitation explicitly so binary transport is not oversold as "handles
arbitrarily large trajectories."

### Ownership
MolSysViewer (frontend interpolation + the existing `partial_coordinates_update`
path). Optional and lower priority than Tier 1.

### Acceptance criteria
1. A trajectory streamed at 5–10 fps renders visibly smoother than the raw stream
   for sphere/point representations, without additional Python-side frame rate.

---

## Tier 3 — GPU-engine rewrites (Mol\* UPSTREAM — out of MolSysViewer scope)

The following items from the original proposals live inside the **Mol\* rendering
engine**, not in MolSysViewer, and would require upstream contributions or a fork:

* Direct `gl.bufferSubData` position overwrite for cartoon/surface (no 1:1
  coordinate→vertex mapping exists; the visual must be re-derived).
* **GPU-compute SASA/SES** (grid voxelization + GPU marching cubes).
* **Shader-based selection / property textures** (decoupling color from geometry
  via a vertex→atom index texture and a 1D/2D property texture, O(1) restyle).
* **Vertex-shader frame interpolation** (double-buffered VBOs + LERP uniform).
* **WebGPU shared storage buffers** for in-browser compute+render.

### Recommendation
Do **not** scope these as MolSysViewer work. If they are wanted, raise them as
Mol\* upstream issues/PRs; MolSysViewer would then consume the capability. Listing
them here prevents re-deriving them as local work.

---

## Tier 4 — "GPU from the notebook": three distinct things, only one is infeasible

"Can we use the GPU from the notebook?" hides three different questions. Lumping
them all under "infeasible" was too coarse — only (a) is truly blocked.

### (a) Zero-copy GPU buffer handoff kernel → browser — INFEASIBLE
`cl_khr_gl_sharing` / WebGPU shared buffers between a Python solver and the
browser assume **shared GPU memory in one process**. In the standard Jupyter
deployment the kernel and the browser are **separate processes, frequently on
separate machines**, and the browser isolates its GPU process in a sandbox even
on the same machine — there is no shared GPU context to map. **Discard for the
Jupyter path.** The only same-process scenario is the standalone Qt (PySide6 +
WebEngine) embedding, and even there it is a major undertaking with uncertain
payoff — revisit only if that product specifically justifies it.

### (b) Kernel-side GPU *preparation* — FEASIBLE, currently unused
The Python kernel can absolutely use *its own* GPU (CuPy / PyTorch / numba-cuda)
to **prepare** data before transport: decimate/downsample, generate or simplify
a mesh, or quantize coordinates on-GPU. This is not zero-copy and the result
still travels over the comm as bytes — but "GPU from the notebook" in this sense
is real and useful, and it composes with Tier 1's compression. Low priority, but
a legitimate option, not an impossibility. Cost: adds an optional heavyweight GPU
dependency on the kernel side — keep it strictly optional.

---

## Tier 5 — Server-side GPU rendering + pixel streaming (FEASIBLE, different architecture)

The industry answer to "the system is too big to ship geometry to the client" is
to **not ship geometry at all**: render on a server-side GPU (headless Mol\* or
another engine) and stream **pixels/video** (H.264 / WebRTC) to the notebook,
mirroring only camera/interaction events back. Precedent: remote VMD, MDsrv,
remote ChimeraX.

* **Pro:** transport cost becomes independent of system size — a 10-atom and a
  10-million-atom system stream the same video bitrate; the client is a thin
  viewport.
* **Con:** needs server-side GPU infrastructure, adds interaction latency, and is
  a *fundamentally different product shape* from the current in-browser Mol\*
  embedding. Not a drop-in.

### Recommendation
Do not build now. Record it as the **escape hatch for the extreme case**: if a
real workload ever exceeds what in-browser Mol\* can hold (see the load-upfront
memory ceiling), this — not more transport tuning — is the architecturally honest
answer. A separate initiative if it ever lands.

---

## Risks and open questions

* **Buffer size / chunking.** A large multi-frame trajectory as one `float32`
  buffer can be hundreds of MB. Open question: does the Jupyter comm impose a
  practical per-message ceiling, and do we need to chunk the initial payload into
  several buffered messages? (The streaming path sidesteps this, but the
  "load all frames upfront" path does not.)
* **Fallback detection.** How is "binary unavailable" detected reliably across
  classic Notebook, JupyterLab, VS Code, Colab, and the standalone-Qt embedding?
  A wrong assumption silently breaks rendering. Prefer an explicit handshake over
  feature-sniffing.
* **Batched-shape reproducibility.** Batching M shapes into one message must not
  collapse their individual identities in `_message_history`; replay/export must
  still reconstruct each shape. The header keeps ids in JSON, but the recording
  discipline (record header, drop buffer) needs a dedicated test.
* **MolSysMT read-only views.** The "thin contract to expose read-only coordinate
  array views" assumes MolSysMT can hand out a `float32` C-contiguous view
  without a copy and with the nm unit contract intact. If the native dtype/order
  differs, a copy is unavoidable on the Python side — which is acceptable (it is
  still one copy, not a JSON expansion) but should be measured, not assumed.
* **dtype precision.** `float32` is sufficient for rendering but is a precision
  reduction vs. the source. Confirm no consumer of the *transport* path needs
  `float64` (export/replay keeps full precision via JSON, so this is
  rendering-only).
* **Interaction with the visibility-delta protocol.** Both optimizations are
  "runtime-only wire forms with a reproducible full state recorded separately";
  confirm they compose cleanly (e.g. a binary coordinate update plus a visibility
  delta in the same tick) and share the record-vs-runtime helpers rather than
  duplicating them.

## Verification strategy

Tier 1 acceptance is measurable; the tests should assert the *mechanism*, not
just behaviour:

1. **Payload-size test (Python).** Load a synthetic N-frame trajectory and assert
   the binary path's transmitted byte count is ≈ `F*N*3*4` plus a small header,
   and is a large constant-factor smaller than the JSON path for the same data.
2. **Binary-path-taken test (Python).** With binary enabled, assert
   `widget.send` is called with a non-empty `buffers` list and a header whose
   `encoding == "binary-f32"`; with binary disabled, assert the legacy JSON
   arrays are emitted and rendering is identical.
3. **Round-trip / decode test (TS).** Feed a known `Float32Array` buffer + header
   into the coordinate handler and assert the per-frame slices match the source
   numbers (and that little-endian is enforced).
4. **Topological-signature guard test (TS).** A buffer whose length is not
   `n_frames * n_atoms * 3` must be rejected (route to full reload), never
   written in place.
5. **Shape-batch reproducibility test (Python).** Send a batched shape set, then
   assert `_message_history` still contains one recoverable entry per shape id so
   replay/export reconstructs all M shapes.
6. **Fallback-parity test.** The exported/replayed artifact is byte-for-byte
   identical whether the live session used binary or JSON transport.

Tier 2 acceptance (smoothness) is harder to assert deterministically; verify the
interpolation math (LERP between two known frames yields the expected midpoint)
in a unit test and treat the perceived-smoothness claim as a manual/QA check.

## Recommended scope (summary)

| Tier | What | Verdict | Owner |
|------|------|---------|-------|
| 1a | Shape-set batching | **Already implemented** — no work | — |
| 1b | Binary + compressed numeric transport (coords + batched-shape arrays; int16/delta, BinaryCIF-aligned) | Do **only once profiled** | MolSysViewer (+ thin MolSysMT contract) |
| 2 | Coordinate-level interpolation + sliding-window streaming | Optional, later; the real answer to the memory ceiling | MolSysViewer |
| 3 | GPU-compute surfaces, shader restyle, VBO bypass, vertex-shader LERP, WebGPU storage | Out of scope | Mol\* upstream |
| 4a | Zero-copy GPU handoff kernel→browser | Infeasible (Jupyter) | n/a (only same-process Qt) |
| 4b | Kernel-side GPU *preparation* (CuPy/Torch) | Feasible, low priority, optional dep | MolSysViewer |
| 5 | Server-side GPU rendering + pixel streaming | Feasible; escape hatch for the extreme case | Separate initiative |

## Prioritization (when to build, if ever)

1. **The document is the deliverable.** Its highest value is already banked:
   it stops Tiers 3, 4a, and 5 from being mistaken for local work. No code is
   required for that value to exist.
2. **Nothing here is a pre-1.0 must-do.** The one item that looked like an easy,
   necessary win (shape batching) is **already implemented**. There is no
   low-hanging fruit left to grab before 1.0.
3. **Everything remaining waits for a triggering benchmark** — a concrete
   system/trajectory that measurably hurts. Without that evidence, 1b/2/4b are
   premature optimization, especially pre-1.0 with addons still pending.
4. **For the extreme case, reach for Tier 5, not more transport tuning.** Once a
   workload exceeds what in-browser Mol\* can hold in memory, no amount of
   encoding helps; server-side rendering is the architecturally honest answer.

**Bottom line:** post-1.0 material. Shape batching (1a) is already done;
binary/compressed numeric transport (1b) is real but should wait for a profile;
Tier 2 (streaming) is the answer to the memory ceiling when it arrives. The GPU
questions resolve cleanly: zero-copy handoff is impossible (4a), kernel-side GPU
prep is possible-but-optional (4b), and server-side rendering (5) is the honest
escape hatch for systems too large to ship to the client. Tiers 3–5 are
documented precisely so they are not pursued as local work by mistake.
