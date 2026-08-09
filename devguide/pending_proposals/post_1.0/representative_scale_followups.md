# Post-1.0 performance architecture

**Status:** proposed. This is the canonical post-1.0 performance strategy.

**Evidence:**
[`../../performance/representative_scale_gate_2026_08.md`](../../performance/representative_scale_gate_2026_08.md).

**Related contracts:**
[`../../data_plane_architecture.md`](../../data_plane_architecture.md) remains
normative for the implemented D0-D4 transport. This proposal does not reopen
that protocol. It extends it from a coordinate-native data plane to a complete,
measured scale strategy.

[`structure_windowing_and_lazy_materialization.md`](structure_windowing_and_lazy_materialization.md)
owns the future semantics of resident versus available structures.
[`zero_copy_visual_rendering.md`](../../archive/zero_copy_visual_rendering.md) is
retained in the archive as historical feasibility analysis; statements there
that all molecular data still travels as JSON predate D4 and are not current
architecture.

## 1. Objective

Make MolSysViewer remain responsive, memory-bounded and scientifically exact as
systems grow from small teaching examples to solvated proteins with hundreds of
thousands of atoms and long sequences of structures.

The objective is not a benchmark slogan such as "500,000 structures at 60 FPS".
It is a set of enforceable properties:

- interaction latency remains bounded and observable;
- memory grows with resident scientific data and an explicit cache window, not
  silently with every structure ever visited;
- topology and structural arrays cross process boundaries once per generation,
  in representations suited to their data;
- no optimization invents box, time, chemical metadata or missing values;
- `view.molsys` remains the complete scientific authority unless a future public
  residency contract explicitly changes that meaning;
- rendering fidelity reductions are explicit policies, never silent scientific
  substitutions;
- work is assigned to MolSysViewer, MolSysMT or Mol* according to where the cost
  actually occurs.

## 2. What the measurements say

The Phase 8 measurements change the optimization order.

At 314,568 atoms, one structure of coordinates occupies about 3.6 MiB as typed
`float32` buffers, while the static topology projection occupies about 25.3 MiB
of JSON and MolSysViewer spends about 1.63 s serializing the molecular payload.
Adding structures grows the coordinate buffer but barely changes this topology
CPU cost. The existing D4 path has already removed nested coordinate lists from
the hot path; the remaining Python-side load cost is mostly the wide, repeated
per-atom topology projection.

At the same scale, a first switch to an unvisited structure can take seconds,
almost entirely inside Mol* state updates, representation geometry and render
preparation. Transport and the presentation barrier are negligible there.
Prewarming every structure would only move the work into startup and retain more
memory.

The browser is the final scale ceiling. Ten structures of 314,568 atoms reached
roughly 5.7 GiB total browser-process RSS under SwiftShader, most of it in the
renderer. A smaller wire format cannot by itself fix representation geometry or
GPU memory.

Therefore there are three separate problems:

1. **Projection:** Python currently expands compact scientific topology into
   repetitive JSON columns.
2. **Materialization:** browser and Mol* construct models and geometry lazily,
   with expensive first visits and insufficiently explicit cache policy.
3. **Rendering:** the selected representation may generate and retain too much
   geometry for the available CPU, GPU and memory budget.

Treating all three as "serialization" would optimize the wrong layer.

## 3. Decisions that should remain closed

### 3.1 Keep `molsysmt.MolSys` as the scientific authority

Do not replace `view.molsys` with a viewer-specific topology object or a
transport DTO. `MolSys` owns topology, structures, units and scientific
operations. A wire representation should be cheap and disposable; it should not
become the canonical in-memory model.

`Topology` already lives inside `MolSys`. Exposing a second authoritative
`view.topology` object would create synchronization and lifetime problems without
removing the structures that the viewer also needs.

### 3.2 The portable JSON projection is not an authority

MolSysViewer builds both its array-native payload and its portable JSON payload
directly from `molsysmt.MolSys`. Product Python uses no intermediate
viewer-specific molecular form, and a source-level regression test enforces
that invariant.

`load_molsys_payload` is a MolSysViewer-owned portable projection used by
fallback and static/export paths. It is disposable wire data, not a candidate
scientific model.

The direction is:

- domain object: `molsysmt.MolSys`;
- current high-volume wire: versioned array-native payload;
- compatibility/export: the direct portable MolSysViewer JSON projection, while
  those targets still require JSON;
- future partial source: a separate, form-neutral source contract, not an
  implicitly incomplete `MolSys`.

No current or future MolSysViewer design depends on an intermediate
viewer-specific molecular form. If a future requirement needs a new portable
scientific representation, specify it from that requirement instead of reviving
an unused intermediate by default.

### 3.3 Do not invent absent scientific data

Missing box and time remain absent. Null values, unknown categories and absent
columns need explicit encoding; they must not be replaced by scientifically
plausible defaults merely to simplify a binary schema.

### 3.4 No global structure prewarm

The default may prefetch a small measured window, but it must not eagerly build
all Mol* structures or all representation geometry. Cache size must be bounded by
bytes or atoms, not only by item count.

### 3.5 No Mol* fork as the first response

Profile against the local Mol* source, build a minimal upstream issue or patch,
and consume upstream capabilities where possible. A long-lived fork is justified
only by a measured product requirement that upstream will not support.

## 4. Horizon A: high-confidence improvements

These changes preserve the public scientific model and build directly on D4.
They are the recommended first post-1.0 work.

### A1. Array-native topology protocol v2

#### Problem

`serialize_static_molsys_payload()` currently emits thirteen atom-length Python
lists plus bonds. Repeated values such as residue names, chain IDs, entity IDs,
component names and molecule names are serialized once per atom. Numeric columns
are converted from NumPy/pandas values to Python objects and then encoded as JSON.

The JSON envelope is not intrinsically the problem. A small JSON schema header is
appropriate. The problem is putting the bulk column data inside it.

#### Design

Define a versioned columnar topology payload:

- a small JSON descriptor containing schema version, row domains, column names,
  logical types, nullability, units where applicable, dictionary references and
  buffer descriptors;
- typed numeric columns (`Int32Array`, `Uint32Array`, or the narrowest lossless
  declared type);
- dictionary-encoded categorical columns with one UTF-8 dictionary blob, offsets
  and typed codes;
- validity bitmaps for real missing values;
- typed bond endpoints and orders;
- omission of optional columns that are wholly absent;
- stable atom, group, component, molecule, chain and entity row domains, so data
  stored once per group is not repeated once per atom;
- explicit atom-to-group and group-to-chain relations instead of denormalized
  repeated labels where Mol* construction permits it.

The schema may borrow ideas from Apache Arrow, BinaryCIF and MMTF, but should not
adopt a large runtime dependency without an A/B result. A purpose-built schema is
reasonable because the required molecular domains are small and stable.

#### Important constraint

Do not merely dictionary-encode the current thirteen atom-length columns. That
reduces bytes but preserves unnecessary per-atom work. First project topology at
its natural domains, then encode.

#### Acceptance

- Exact equality of every represented value, including null/absent distinctions.
- Golden decode into the same Mol* model properties as protocol v1.
- At 104,856 and 314,568 atoms: record Python projection time, encoding time,
  metadata and buffer bytes, browser decode time, main-thread blocking,
  first-visible time and peak RSS.
- Target at 314,568 atoms: at least 4x fewer topology wire bytes and 3x faster
  Python topology preparation than the Phase 8 baseline. These are hypothesis
  gates, not promises; revise them before implementation only from a recorded
  prototype.
- Protocol v1 remains a bounded reader during migration, not an unbounded second
  implementation.

### A2. Topology projection cache by generation

Topology is static across structure changes and usually across popup creation,
reconnection and repeated rendering endpoints. Serialize it once per topology
generation.

Add an immutable projection object keyed by an explicit topology generation or
fingerprint. Cache:

- columnar topology descriptors;
- encoded topology buffers;
- optional Mol*-ready derived identifiers that are independent of coordinates.

Invalidate on topology edits, not on frame/structure changes, scene mutations or
camera changes. Use bounded ownership: the current generation plus in-flight
deliveries, released when no endpoint references it.

Do not hash every topology byte on every request. MolSysMT should eventually
provide a cheap mutation generation; until then MolSysViewer can own a generation
counter around the topology-edit paths it controls.

Acceptance: opening a second endpoint or sending a new structural generation with
the same topology performs zero full topology reprojections, proven by a spy on
the projector and by retained-memory accounting.

### A3. Move preparation away from interactive critical sections

Widget sends remain on the kernel/main thread because the connector is not
thread-safe. Pure preparation need not.

Prototype:

- vectorized NumPy preparation that releases the GIL;
- a bounded worker for dictionary construction and encoding;
- cancellation by molecular generation;
- main-thread publication only after the prepared generation is complete.

Do not introduce a worker merely to hide the same latency. It is accepted only if
camera/UI commands remain responsive during preparation and cancellation releases
buffers promptly. A Rust extension is not justified until profiling proves the
remaining encoder is CPU-bound after domain normalization and NumPy vectorization.

### A4. Browser decode off the main thread

Decode topology dictionaries, validate descriptors and prepare transferable
columns in a Web Worker. Transfer `ArrayBuffer` ownership to the runtime; do not
copy it back to the host. Keep Mol* state mutation on the main thread.

This only helps if decode or object construction blocks interaction. Measure long
tasks before adding the worker. The worker protocol must use the same molecular
generation, cancellation and endpoint ownership rules as D4.

### A5. Instrument the real critical path

Add durable timings for:

- MolSysMT access/projection;
- topology normalization and encoding;
- coordinate conversion and layout;
- transport enqueue, first byte and completion;
- browser decode;
- Mol* parse/model/structure transforms;
- representation geometry and GPU upload;
- first visible frame;
- unvisited and revisited structure changes.

Record bytes and retained memory beside time. A faster stage that doubles retained
memory is not an unqualified improvement.

## 5. Horizon B: bounded materialization and adaptive rendering

These changes can produce larger gains but require explicit behavior contracts.

### B1. Bounded structure cache and predictive prefetch

For already resident structures, compare:

1. no prefetch;
2. next-one prefetch;
3. direction-aware current +/- N prefetch;
4. a byte-bounded LRU of prepared Mol* structures or representation data.

Prefetch is low-priority and cancellable. Direct interaction always wins. The
cache budget is expressed in bytes/atoms and can react to browser memory pressure.
It must distinguish first visit from revisit in telemetry.

The first implementation should not guess at a universal N. Systems and
representations have different geometry costs.

### B2. Interaction-quality and idle-quality tiers

Large molecular scenes need an explicit render policy, not one fixed quality for
all hardware and all interactions.

Possible policy:

- while rotating, scrubbing or resizing: lower sampling/quality, defer expensive
  representation rebuilds and cap visual detail;
- after a short idle barrier: restore the requested final representation quality;
- for solvent-heavy systems: offer explicit solvent coarse-graining or hiding,
  never automatic deletion;
- use Mol* impostors and built-in quality controls where they preserve the chosen
  representation semantics;
- expose diagnostics when Mol* substitutes a representation because the requested
  one is not drawable for that component.

The user-visible setting remains the final scientific scene. Interaction quality
is transient endpoint state and is not serialized as if it were the requested
representation.

### B3. Spatially aware level of detail

For million-atom scenes, detail should depend on relevance, not only atom count:

- full detail for selected/focused regions;
- reduced representation for distant solvent or bulk environment;
- spatial chunks or tiles with conservative bounds;
- frustum and occlusion-informed preparation where Mol* can expose it;
- progressive refinement from a scientifically declared coarse representation to
  the final scene.

This requires a visual fidelity contract. A backbone-only preview cannot claim to
be the final all-atom scene. Picking and selections must resolve to stable original
atom identities even when geometry is coarse.

### B4. Mol* first-visit optimization

Use the local Mol* source to locate the measured 0.15-13 s unvisited-structure
cost among boundary computation, remapping, state transforms, representation
geometry and GPU upload.

Potential upstream work:

- reusable topology-invariant model/structure data across structures;
- explicit prepare-next-structure task with cancellation;
- byte-accounted representation caches;
- reusable geometry buffers when only coordinates change;
- GPU timing and retained-resource diagnostics;
- progressive or chunked representation updates.

Only propose a Mol* patch after a mutation/A-B benchmark identifies its owning
stage. Transport changes cannot close a geometry bottleneck.

## 6. Horizon C: MolSysMT source and encoding contract

MolSysMT should not become aware of MolSysViewer messages or Mol* types. It can,
however, expose scientific data in a form that avoids repeated conversion by all
consumers.

### C1. Form-neutral columnar topology view

Propose upstream in `molsysmt/devguide/pending_proposals` an API that returns
read-only, domain-correct topology columns:

- explicit row domain (`atom`, `group`, `component`, `molecule`, `chain`,
  `entity`, `bond`);
- contiguous numeric arrays where available;
- categorical values either as arrays or dictionary codes;
- validity information without coercing missing values;
- stable identity/order contract;
- topology generation/fingerprint;
- no viewer-specific transport form and no dependency on MolSysViewer.

MolSysViewer can encode that view into protocol v2. Other clients can use it for
analysis, storage or different visualizers. This is a better upstream abstraction
than standardizing a viewer transport representation.

### C2. Exact structural block API

For later partial residency, MolSysMT needs a form-neutral source interface:

```text
read_structures(structure_indices)
  -> coordinates + optional box + optional time
     with explicit units, dtype, shape, ordering and ownership
```

It must advertise random-access versus sequential-only capability and define
cancellation/lifetime. It must not call every sequence a trajectory. This is the
upstream prerequisite owned in
[`structure_windowing_and_lazy_materialization.md`](structure_windowing_and_lazy_materialization.md).

### C3. A standardized scientific molecular serialization

A portable MolSysMT serialization can be valuable for persistence and interchange,
provided it is designed as a scientific format rather than a viewer payload.

It should separate:

- a versioned semantic schema;
- compact binary/columnar storage;
- optional human-readable metadata;
- topology from structures;
- provenance and units from transport envelopes.

Possible implementations include Arrow IPC, HDF5/Zarr, BinaryCIF-compatible
columns or a small custom container. Selection requires measurements of read
latency, partial access, ecosystem cost and exact round-trip behavior. MolSysViewer
should consume such a format through MolSysMT, not own it.

## 7. Horizon D: ambitious research directions

These are credible directions, not approved implementation commitments.

### D1. Shared schema and codec across Python and browser

Define one declarative molecular column schema and generate:

- Python validation/encoding;
- TypeScript types and decoding;
- test vectors;
- optional Rust/WASM high-performance codec.

This removes hand-maintained schema drift and allows identical dictionary/null
semantics on both sides. It is high effort but has value beyond speed: protocol
evolution becomes safer.

### D2. Local shared memory for desktop Qt

For local desktop only, investigate memory-mapped files or OS shared memory for
large immutable payloads, with descriptors sent over the Qt bridge. This could
avoid the current 2x assembly peak near the 256 MiB warning.

It does not apply to remote Jupyter kernels and needs strict lifetime, permission,
cleanup and crash-recovery rules. Keep the normal binary stream as fallback.

### D3. WebGPU and GPU-resident structure updates

Long-term gains may require Mol* or another engine to keep coordinate arrays and
some representation work GPU-resident. Candidate research:

- WebGPU storage buffers for structure coordinates;
- compute-based culling and level-of-detail selection;
- GPU interpolation between structures;
- indirect drawing of spatial chunks;
- reuse of representation buffers across coordinate-only changes.

This is upstream rendering-engine work. Browser support, numerical behavior,
picking and fallback parity must be demonstrated before product adoption.

### D4. Remote rendering for extreme workloads

For systems beyond browser memory, an optional server-rendered mode could keep the
scientific system and geometry near a GPU server and stream pixels plus picking
metadata. It trades local interactivity and offline reproducibility for a much
higher scale ceiling.

This should be a separate deployment mode, not hidden behind the normal widget
API. It introduces authentication, resource scheduling, latency and reproducible
session concerns and is therefore a research horizon, not a default architecture.

### D5. Progressive molecular scene compilation

Treat scene construction as a cancellable compiler pipeline:

```text
MolSys/source
  -> exact topology IR
  -> resident structure window
  -> semantic scene IR
  -> endpoint-specific Mol* plan
  -> progressive geometry
```

Each stage has generation identity, cache ownership, byte budget and observable
timings. This would let canvas, popup, Qt, static export and future renderers share
scientific semantics while choosing different materialization strategies. It is
the most ambitious direction, but also the cleanest long-term growth model.

## 8. Work ownership

| Problem | Primary owner | Why |
|---|---|---|
| Array-native topology v2 and endpoint transport | MolSysViewer | Wire and browser consumption are viewer concerns |
| Natural-domain columns and exact structural blocks | MolSysMT | Scientific forms and units must be viewer-independent |
| Model/geometry first-visit cost and GPU resources | Mol* upstream | The measured cost is inside the rendering engine |
| Structure-window user semantics | MolSysViewer + MolSysMT | Viewer policy depends on source capabilities |
| Portable scientific file format | MolSysMT | It must serve more than one viewer |
| Qt shared-memory connector | MolSysViewer | Connector-specific local optimization |

Do not hide an upstream bottleneck behind a local cache indefinitely. Record a
minimal profile and write the proposal in the owning repository.

## 9. Recommended execution order

### P0. Baseline and observability

- Preserve the Phase 8 fixtures and add hardware/browser descriptors.
- Add stage timings and main-thread long-task capture.
- Set acceptance thresholds before seeing each optimization result.

### P1. Topology v2 prototype

- Prototype natural-domain columns on 104,856 and 314,568 atoms.
- Compare custom columnar, Arrow-inspired and BinaryCIF-aligned encodings without
  committing to a dependency.
- Write the companion MolSysMT proposal from measured API friction.

### P2. Production topology path

- Versioned schema, generated validators/types if justified.
- Projection cache by topology generation.
- Worker decode only if the main-thread profile requires it.
- Compatibility and real-Mol* E2E.

### P3. Mol* first-visit and adaptive rendering

- Attribute the unvisited-structure latency.
- A/B bounded prefetch/LRU.
- Add interaction-quality policy using existing Mol* capabilities.
- Open upstream work for the remaining engine-owned stage.

### P4. Decide structure residency

- Complete the source/resident public contract.
- Prototype a bounded structural window against at least native `MolSys`, one
  random-access file source and one sequential-only source.
- Preserve exact atom identity and absence of box/time.

### P5. Research prototypes

- Shared generated schema/codec.
- Qt shared memory.
- WebGPU or remote rendering only with a concrete scientific workload that
  exceeds the earlier horizons.

## 10. Performance and correctness gates

Every optimization report must include:

- fixture atom and structure counts, topology composition and representation;
- cold/warm distinction and first-visit/revisit distinction;
- wall-clock distributions, not a single profiled duration;
- wire bytes, peak RSS, retained RSS and browser renderer memory;
- main-thread long tasks and first-visible time;
- cache state and invalidation event;
- exact scientific round-trip checks;
- behavior when box, time or optional topology fields are absent;
- cancellation and stale-generation tests;
- real Mol* browser validation for render claims.

Profiled durations are not wall-clock evidence. Compression ratios without
encode/decode CPU and retained-memory measurements are not performance evidence.

## 11. Explicit non-goals

- Replacing `molsysmt.MolSys` with a wire projection.
- Calling all structure sequences trajectories.
- Claiming end-to-end zero-copy across a remote Jupyter boundary.
- Lowering precision or dropping atoms silently.
- Prebuilding every structure or representation.
- Introducing Arrow, Rust, WebGPU or a Mol* fork because they are fashionable.
- Optimizing transport to explain a bottleneck measured inside Mol* geometry.

## 12. Expected result

The realistic near-term gain is substantial: topology preparation and transfer
can become several times smaller and faster, repeated endpoints can reuse one
projection, and first-visit work can be bounded instead of globally prewarmed.

The larger horizon is not "a faster JSON viewer". It is a molecular scene system
with a complete scientific authority, a compact columnar projection, bounded
structure residency, endpoint-specific compilation and a rendering engine that
can progressively spend detail where it matters. That architecture can grow from
notebooks to desktop, remote and future GPU-backed modes without changing the
scientific meaning of the scene.
