# Array-native data plane for materialized structures

**Status:** complete for pre-1.0. D0 through D4 are implemented and
mutation-verified on the AnyWidget connector, and Qt now has both its own
baseline (`../performance/qt_transport_baseline_2026_07.md`) and binary
transport, served through the payload scheme handler it already had.

Both connectors keep the JSON path as an observable fallback. Windowed
residency stays post-1.0; `SharedArrayBuffer` is blocked on preconditions this
project does not own.

Promoted out of `pending_proposals/` on 2026-08-05: ten documents cite it as the
current description of the data plane, `architecture.md` and `roadmap.md` among
them, which is a contract's job and not a plan's.

**Scope:** connector-neutral transport of large homogeneous numeric arrays
between Python and TypeScript. MolSysViewer 1.0 continues to materialize every
selected structure in `view.molsys`. Lazy sources, partial residency, and
eager/windowed modes belong to
[`post_1.0/structure_windowing_and_lazy_materialization.md`](pending_proposals/post_1.0/structure_windowing_and_lazy_materialization.md).
Runtime routing belongs to
[`runtime_message_router.md`](runtime_message_router.md).

## Decision

MolSysViewer keeps:

- **scientific model:** the complete selected `molsysmt.MolSys`;
- **control plane:** JSON-like scene operations, events, acknowledgements,
  errors, and small projections;
- **data plane:** typed binary buffers for structural numeric arrays;
- **compatibility path:** the current JSON molecular payload.

The optimization removes `ViewerJSON`, nested Python lists, and text JSON from
the coordinate hot path when a connector supports buffers. It does not change
which structures are loaded or available to Python, Mol*, playback, add-ons, or
scientific methods.

This binary path is already implemented for the embedded AnyWidget canvas. It
is not merely preparation in `widget.py` or `history.py`: the serializer,
typed-buffer decoder, chunk lifecycle, acknowledgements, cancellation, JSON
fallback, and real-browser Mol* validation are present. Remaining work closes
the implementation rather than starting it.

## Evidence

The July 2026 baseline is recorded in
[`../performance/trajectory_transport_baseline_2026_07.md`](performance/trajectory_transport_baseline_2026_07.md).
For 5,000 structures of only 62 atoms it measured:

- 18.37 MB JSON;
- about 7.97 s Python preparation;
- 752 MB peak Python RSS;
- about 385 ms browser fetch plus JSON parsing.

The Python stages after `msm.convert` included roughly 1.61 s converting to
`ViewerJSON`, 2.12 s normalizing nested lists, and 0.69 s encoding JSON.
Those stages are avoidable without changing residency semantics.

Scale must be evaluated across both independent axes:

- many atoms and few structures;
- few atoms and many structures;
- a representative combination.

One 100,000-atom coordinate structure is 1.2 MB as `float32`; 100 structures are
120 MB raw before Mol* and browser overhead. Binary transport reduces
amplification, but it does not make complete materialization bounded.
Likewise, an extremely long sequence of materialized structures is not made
bounded merely by calling it a trajectory or sending it as `Float32Array`.
MolSysMT's contract is expressed in structures; playback may interpret an
ordered sequence as a trajectory, but lazy/windowed residency remains a
separate post-1.0 design.

## Structural data envelope

```json
{
  "op": "structure_data_chunk",
  "protocol_version": 1,
  "viewer_id": "view-...",
  "session_id": "session-...",
  "stream_id": "structures:main",
  "generation": 3,
  "chunk_id": 17,
  "kind": "coordinates",
  "dtype": "float32",
  "shape": [12, 3, 100000],
  "layout": "structure-planar-c",
  "structure_start": 0,
  "structure_count": 12,
  "units": "angstrom",
  "endianness": "little",
  "buffer_index": 0,
  "byte_length": 14400000
}
```

### Coordinate layout: planar, for zero-copy frames

Coordinates travel as `structure-planar-c`: per structure, all x, then all y,
then all z, with shape `[structures, 3, atoms]`. Box and time keep
`structure-major-c`.

The reason is the consumer, not the producer. Mol\* frames want separate
per-axis arrays, so an interleaved `xyzxyz…` buffer forces the frontend to
de-interleave every frame: three fresh `Float32Array` allocations per structure
plus an element-by-element scalar copy. On 5,000 structures of 62 atoms that was
930,000 scalar assignments and 15,000 allocations; on 100 structures of 100,000
atoms it is 30 million assignments and a second full copy of the coordinates
(the transient peak doubles).

With the planar layout the frontend takes `subarray` **views** instead: no
de-interleaving pass, no second allocation, and the transient peak drops to the
received buffer alone. The cost on the Python side is nil — the transpose fuses
into the contiguous `float32` conversion that already happened (measured 44.8 ms
versus 43.3 ms for the same case, within noise).

Mol\* may reorder a frame's axes in place, which is safe for views because each
frame spans a disjoint range and the buffer is not reused after loading. A real
browser E2E asserts that typed views build a working Mol\* trajectory.

Requirements:

- identity, generation, chunk, structure range, and numeric metadata are
  mandatory;
- dtype, shape, layout, units, endianness, buffer index, and byte length are
  validated before use;
- coordinates preserve the existing MolSysViewer-to-Mol* wire unit, angstrom;
- structure ordering exactly matches the selected `structure_indices`;
- box and time retain their structure-axis alignment;
- stale generations, duplicate chunks, malformed lengths, cancellation, and
  connector failure are observable;
- chunks may split delivery for backpressure, but the frontend ultimately
  receives every selected structure;
- binary buffers are runtime transport, not scene-history entries.

`float32` is the first coordinate wire dtype. Python scientific arrays retain
their canonical precision. This is not an end-to-end zero-copy claim.

## Capability negotiation and fallback

```json
{
  "event": "ready",
  "capabilities": {
    "binary_structure_data": [1],
    "max_buffer_bytes": 16777216,
    "transferable_array_buffer": true
  }
}
```

Python selects the highest mutually supported version. If none exists, it sends
the current JSON payload with identical structures and scene behavior.

Capabilities are endpoint-local. AnyWidget, Qt, docs, embedded canvases, and
popup canvases may select different transport adapters without changing the
scientific model.

## Array-native Python path

The binary path obtains structural data directly from `view.molsys`:

1. serialize topology/static columns once;
2. obtain coordinates as an ndarray in nm;
3. convert once to C-contiguous `float32` in angstrom;
4. send the backing bytes with the descriptor;
5. transport box and time as aligned arrays when present.

It must not route coordinates through:

- `MolSys.to_form("molsysmt.ViewerJSON")`;
- `.tolist()`;
- a second per-coordinate normalization loop;
- `json.dumps()` of numeric coordinates.

`ViewerJSON` remains available for fallback, export, and interoperability.

## Connector and popup behavior

- **AnyWidget:** custom messages with binary buffers.
- **Qt:** current payload references remain the initial fallback. Alternative
  binary mechanisms require their own benchmark.
- **Popup:** the runtime router sends one current molecular projection to a
  canvas popup; it does not accumulate molecular payloads in a replay log.
- **Panel popup:** receives UI state and no molecular arrays.
- **HTML/docs export:** remains portable and JSON-based unless a separate
  embedded-asset contract is approved.

## Reproducibility and lifecycle

- state v2 and HTML export remain JSON-serializable;
- `_message_history` records reproducible intent, not transient buffers;
- replay reconstructs the same complete selected system;
- a generation replacement invalidates old chunks;
- receiver resources are released on cancellation, rebuild, endpoint close, and
  view close;
- fallback and binary transports produce equivalent Mol* structures.

## Implementation slices

### D0. Fixtures and budgets

- preserve the existing small-sequence baseline;
- add a solvated topology near 100,000 atoms;
- cover many-atoms/few-structures and few-atoms/many-structures separately;
- measure MolSysMT conversion, array preparation, transfer, decode, Mol*
  construction/update, Python RSS, browser heap, and raw byte counts.

### D1. Array-native serializer

- separate topology/static serialization from structural arrays;
- convert coordinates once into contiguous `float32` angstroms;
- preserve exact box, time, shape, units, and ordering;
- retain the current JSON serializer unchanged as fallback.

Implemented in `molsysviewer/loaders/array_native_molsys.py`. The serializer:

- reads all materialized coordinates directly from `MolSys.structures`;
- emits C-contiguous little-endian `float32` coordinates in angstroms;
- emits aligned box and time arrays only when they exist in the `MolSys`;
- does not invent box or time for systems that lack them;
- serializes static topology without converting the complete `MolSys` to
  `ViewerJSON`;
- returns metadata plus ordered memory buffers without sending or recording
  them.

The live AnyWidget loader uses this path when the negotiated endpoint supports
protocol version 1. JSON remains the compatibility and reproducibility path.

### D1 preliminary measurement

On the same 5,000-structure, 62-atom pentalanine case used by D0, after
`msm.convert` had already produced the complete `MolSys`, D1 measured:

- 43.3 ms to prepare coordinates, box, time, and static metadata;
- 3.94 MB of structural buffers: 3.72 MB coordinates, 0.18 MB box, and
  0.04 MB time.

The prior JSON path measured 1.61 s for `ViewerJSON`, 2.12 s for nested-list
normalization, 0.69 s for JSON encoding, and 18.37 MB on the wire. This is
evidence that D1 removes the targeted Python amplification. It does not yet
measure AnyWidget delivery, browser decoding, Mol* construction, retained
memory, or large-topology behavior.

### D2. AnyWidget binary slice

- add a private buffer-send seam beside the control-plane send path;
- negotiate capability version 1;
- deliver all selected structures, splitting only for transport limits;
- validate malformed, duplicate, stale, cancelled, and late chunks.

#### D2a implemented: typed delivery and direct Mol* construction

The AnyWidget frontend now advertises protocol version 1 and a per-buffer
limit. Python retains `load_molsys_payload` in `_message_history`, state v2, and
HTML export, but replaces only the live delivery with
`load_molsys_array_payload` plus AnyWidget binary buffers. The frontend:

- validates identity, protocol, dimensions, dtype, units, layout, endianness,
  buffer ownership, and byte lengths;
- constructs Mol* coordinate frames directly from `Float32Array` data;
- retains exact optional box and time arrays when present;
- never rebuilds the structural coordinate axis as nested JavaScript arrays.

The binary path is currently advertised only when `enable_popout=False`.
Canvas popouts still depend on one compacted current JSON molecular projection;
silently opening an empty popup would be a functional regression, while
retaining a second nested JSON copy would defeat the memory objective. The
popup replay no longer accumulates superseded molecular generations or
high-frequency state, and panel popups receive no molecular projection. Popup
binary parity belongs to D4.
With popout enabled, unsupported capabilities, malformed capability metadata,
or a buffer above the negotiated 16 MiB D2a limit, Python uses the unchanged
JSON path.

Validation:

- Python tests prove capability negotiation, binary buffer delivery, history
  isolation, and JSON fallback;
- TypeScript tests reject duplicate descriptors, aliased buffer indices,
  malformed lengths, and inconsistent complete envelopes;
- `array-native-load.e2e.ts` confirms in Chrome/WebGL that typed buffers create
  a real two-structure Mol* trajectory.

#### D2b implemented: lifecycle and splitting

Python splits on the structures axis so every individual buffer remains below
the negotiated endpoint limit. A `structure_data_begin` handshake precedes
delivery, only one chunk is in flight, and every accepted chunk must be
acknowledged before the next is sent. The receiver preallocates the complete
typed arrays and rejects mismatched identity, stale generations, duplicate or
non-contiguous chunks, undeclared arrays, invalid descriptors, cancellation,
and late delivery. Replacement, view disposal, connector failure, and
frontend rejection release the retained payload; connector/frontend failure
falls back observably to the recorded JSON load.

The real-browser E2E assembles two chunks and verifies that the resulting
typed payload creates a 3-atom, 2-structure Mol* trajectory.

### D3. Backpressure and cleanup

- enforce maximum buffer bytes and maximum in-flight chunks;
- acknowledge accepted chunks and cancel failed generations;
- measure transient peaks separately from final retained molecular data;
- release all resources deterministically.

The buffer ceiling, one-chunk-in-flight discipline, acknowledgements, and
explicit replacement/cancellation cleanup are implemented.

#### D3 implemented: acknowledgement timeout and observable release

A frontend that never acknowledges used to pin the retained `float32` arrays
forever: the stream sat in `awaiting: "begin"` with no fallback. Each stream now
carries a deadline (`_binary_ack_timeout_s`, 30 s by default) that restarts on
every accepted acknowledgement, so a peer that is merely slow is not mistaken
for a dead one.

The deadline is evaluated **on main-thread entry points only** — the inbound
frontend message path, a new molecular load, and the binary-event handler. There
is deliberately no timer thread: `widget.send` is not safe to call off the
kernel thread for AnyWidget, so a `threading.Timer` firing a send would create
exactly the unsafe cross-thread delivery this slice must avoid. The accepted
consequence is that a fully idle kernel does not fire the timeout; with an idle
kernel nothing is competing for that memory either. The check is deliberately
absent from `_send_widget_message`, because the fallback path itself sends and
would re-enter.

On expiry `_release_binary_structure_stream` drops the chunk memoryviews and
their parent ndarrays explicitly rather than waiting for the dict to fall out of
scope, a `structure_data_cancel` tells the receiver to drop its half, and the
recorded JSON load is delivered with a `RuntimeWarning` — the same observable
path as a connector failure. Completion and cancellation release through the
same helper.

Audit note: the only `threading.Thread` in the package serves headless image
export over HTTP and never touches the widget, and playback is driven by the
frontend rather than a Python timer, so no unsafe cross-thread send existed to
begin with. A regression test asserts the timeout path sends on the calling
thread.

#### In-flight window: measured and deliberately left at one

`maximum in-flight chunks` is fixed at one. Widening it to a credit window was
measured rather than assumed:

| case | coordinates | chunks at 16 MiB |
|---|---|---|
| 5,000 x 62 atoms | 3.7 MB | 1 |
| 100 x 100,000 atoms | 120 MB | 8 |
| 1,000 x 100,000 atoms | 1.2 GB | 77 |

Serialized round trips cost 8 x RTT and 77 x RTT respectively — roughly 40 ms
and 300 ms at a 5 ms RTT. Against that, transferring a 16 MiB buffer itself
dominates, so a window would recover single-digit percentages on large loads and
nothing at all on the common case, which fits in one chunk.

It is left at one because the cost is real: the receiver's strict contiguity
check, Python's single `awaiting` state, and D3's per-chunk deadline all become
window-aware, in exactly the code path where D3 just added safety. The 1.2 GB
row is better answered by windowed residency (post-1.0) than by pipelining a
transfer that should not happen in full. Recorded here as a known lever rather
than an oversight.

#### D3 implemented: transient versus retained memory

`resource.getrusage(...).ru_maxrss` is a monotonic high-water mark, so the
existing baseline could report a peak but never tell how much of it was
released. The benchmark now also reads current RSS from `/proc/self/statm` and
reports `peak_rss_growth`, `retained_growth`, and the derived
`transient_growth`. A transport is acceptable only when the peak is bounded
*and* the retained footprint matches the science rather than the wire format.

The numbers describe resident memory at the end of a case, with the payload
still referenced; they are a transport comparison, not a viewer-lifetime
measurement. Structural release of the stream's own arrays is asserted directly
by the acknowledgement-timeout tests.

### D4. Endpoint parity

#### D4b implemented: typed molecular generation for a canvas popup

A canvas popup now receives its molecular generation as typed buffers instead of
a second JSON copy, which lifts the compromise that disabled the binary path
entirely whenever `enable_popout` was set.

The delivery is **Python-originated and endpoint-addressed**. When a canvas popup
asks for its scene snapshot (the R2 request), Python starts an array-native
stream carrying `target_endpoint_id`, and the snapshot then omits
`load_molsys_payload` so the same scene never travels twice. The widget host sees
a message addressed to an endpoint that is not itself and **relays** it through
`sendTo` rather than consuming it; the popup assembles the chunks with its own
`ArrayNativeStreamReceiver` and acknowledges back through the host, so Python
drives the next chunk and flow control holds end to end.

The alternative — the host retaining its decoded generation to forward on demand
— was rejected on memory grounds. `splitInterleavedPositions` used to copy into
Mol\*-owned axes, so the host retains nothing today; keeping a spare full copy
would have added a permanent tax (120 MB on a 100 x 100,000-atom system) *even
when no popup is ever opened*. With Python re-streaming instead, the host holds
one chunk transiently while relaying, bounded by the one-chunk-in-flight rule,
and no endpoint keeps a spare generation.

At most one binary stream is in flight **per endpoint**. Each destination owns
its transfer manager, acknowledgement deadline and deferred scene queue, so a
canvas bootstrap does not stall projections for the embedded host. The manager
persists inactive across completed or fallback generations until its endpoint
closes; this preserves the monotonic generation identity retained by the live
receiver. A popup-targeted stream that fails falls back to a JSON load
**addressed to the popup**, never into the host, which already holds that
structure.

What remains inherent: two Mol\* instances each keep their own axes, so browser
memory is roughly 2x the coordinates while a canvas popup is open. No transport
choice changes that — it is the cost of a second renderer with its own WebGL
context. `SharedArrayBuffer` is the only real answer and needs cross-origin
isolation that Jupyter does not provide by default, so it stays post-1.0
alongside windowed residency.

Verified in a real browser by `structure-data-relay.e2e.ts`, which opens an
actual popup and checks the part the other E2Es do not cover: that binary buffers
survive the `postMessage` seam **byte for byte**, that only the addressed
endpoint receives them (a panel-addressed relay with no panel open lands
nowhere), that the chunk identity is preserved, and that the popup's
acknowledgement returns through the host. Mutation-verified: corrupting the
relayed buffer fails the byte comparison.

Qt keeps the JSON path and still requires its own benchmark; AnyWidget success
does not imply it.

- route descriptors through the common runtime router;
- validate popup behavior;
- retain Qt and docs fallbacks until connector-specific binary paths prove
  useful and reliable.

## Remaining execution order

**Corrected 2026-08-06.** Items 1 to 3 below were listed as remaining while the
header of this same file said D0-D4 were complete. They are done, and each is
described in its own section above: R2's canonical popup snapshot, D3's
acknowledgement timeout with observable release, and D4's endpoint parity —
`tests/test_runtime_seam_integration.py::test_a_canvas_popup_snapshot_streams_the_molecular_generation_to_its_endpoint`
pins the last of them.

A file contradicting itself is worse than a file that is merely out of date: a
reader who lands in the middle believes the middle. This is what
`transport_popup_audit_followups_2026_08.md` item 5 was about.

1. ~~Finish R2's canonical popup snapshot.~~ **Done.**
2. ~~Close D3 with a no-ack timeout plus memory measurements.~~ **Done**, and the
   timeout's cooperative semantics are stated under *D3 implemented* above.
3. ~~Implement D4 endpoint parity.~~ **Done.**
4. Keep partial residency, structure windows, cache eviction, and
   demand-driven access post-1.0. They require a separate scientific and public
   API contract and are not implied by binary transport. **This is the only one
   still open, and it is post-1.0 by decision.**

## Acceptance criteria

- `view.molsys` remains a complete selected `molsysmt.MolSys`;
- binary and JSON paths expose exactly the same structures and ordering;
- coordinates avoid `ViewerJSON`, nested lists, and text JSON on the binary path;
- the large fixtures show reduced preparation time, transferred bytes, and
  transient memory amplification;
- topology, coordinates, box, time, units, and precision expectations are
  tested;
- malformed, duplicate, stale, cancelled, and late chunks fail observably;
- two viewers and popup endpoints cannot consume each other's buffers;
- state, history, replay, and export semantics remain unchanged;
- no performance claim is inferred solely from typed-array construction.

## Pre-1.0 scale guard: an honest ceiling instead of a silent death

1.0 materializes every selected structure on purpose; windowed residency would
change what `view.molsys` means and stays post-1.0. But until this slice there
was **no guard of any kind**: asking for a 1.2 GB trajectory simply tried, until
the browser tab or the kernel died, with no warning.

That absence — not the absence of windowing — was the 1.0 defect. What 1.0 owes
the user is a ceiling that is *known, measured and actionable*.

`molsysviewer/_private/scale_budget.py` computes the coordinate cost
(`atoms x structures x 3 x float32`, the one quantity that scales with both
axes) and warns when it exceeds a budget, naming the size, noting that a canvas
popup doubles the renderer-side cost, and giving a concrete
`structure_indices=range(0, N, stride)` that fits. The default ceiling is 256 MB
of coordinates.

It **warns and never refuses**: only the caller knows whether their machine can
hold it, and silently declining scientific data would be worse than a heavy
load. `molsysviewer.config.set_structure_scale_budget(bytes)` raises or lowers it, and
`0` silences it.

Surfaced by this work: `load_from_molsysmt` read the structure count through
`structures.get_n_structures()`, which does not exist. The call always raised,
the surrounding `except Exception` swallowed it, and `n_structures` silently
stayed `None` until it was recovered later by counting the serialized payload.
Fixed to the `structures.n_structures` attribute.

## Blocked rather than merely deferred: SharedArrayBuffer

`SharedArrayBuffer` is the only mechanism that would remove the 2x browser
memory of two Mol\* instances. It is listed below as post-1.0, but "post-1.0"
undersells it: it is blocked on three preconditions, **none of which this
project owns**.

- **The headers are not ours.** `SharedArrayBuffer` requires cross-origin
  isolation (COOP + COEP), which is server configuration of the notebook host.
  Requiring users to reconfigure JupyterLab to open a viewer is not a reasonable
  ask, and `COEP: require-corp` breaks any cross-origin resource without CORP
  headers — it would break unrelated content in the user's own notebooks. (The
  interaction between `COOP: same-origin` and the `window.opener` the popup
  handshake depends on also needs verifying, and would be fatal if it severs.)
- **Mol\* mutates coordinate arrays in place.** `reorderCoordsInPlace` reorders
  a frame's axes. Two Mol\* instances sharing one buffer, either of which may
  reorder, is silent corruption. Sharing needs an upstream guarantee we do not
  have.
- **The payoff is narrow**: it only helps while a canvas popup is open, which is
  an opt-in secondary window.

Recording it as "blocked on external preconditions" is more useful than a date,
because no amount of work on our side unblocks it.

## Explicitly post-1.0

- lazy structure sources and partial residency;
- eager/windowed modes, cache eviction, and demand-driven structure access;
- lossy quantization, delta compression, and interpolation;
- worker offload;
- shared-memory or memory-mapped Qt transport;
- arbitrary scientific arrays beyond the first accepted kinds;
- sustained-FPS and end-to-end zero-copy claims.

## Related work

- [`runtime_message_router.md`](runtime_message_router.md)
- [`post_1.0/structure_windowing_and_lazy_materialization.md`](pending_proposals/post_1.0/structure_windowing_and_lazy_materialization.md)
- [`post_1.0/zero_copy_visual_rendering.md`](pending_proposals/post_1.0/zero_copy_visual_rendering.md)
- [`../performance/trajectory_transport_baseline_2026_07.md`](performance/trajectory_transport_baseline_2026_07.md)
