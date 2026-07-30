# Pending proposals

Only unresolved designs belong here. Implemented plans are promoted to durable
documentation or removed; Git retains their development history.

## Before 1.0

Two accepted pre-1.0 improvements are active:

- [`data_plane_architecture.md`](data_plane_architecture.md): typed buffers for
  already materialized structural arrays, with behaviorally equivalent JSON
  fallback;
- [`runtime_message_router.md`](runtime_message_router.md): one authority and a
  typed route across Python, widget/Qt hosts, canvases, and popups.

They preserve the current 1.0 scientific model: `view.molsys` remains a complete
selected `molsysmt.MolSys`. The data-plane work removes avoidable
`ViewerJSON`/nested-list/text-JSON amplification without introducing partial
residency.

Structure windowing, eager/windowed modes, compression, workers, shared memory,
BroadcastChannel, and multiview remain post-1.0. Camera acquisition/movie export
is also explicitly post-1.0.

## Deferred until after 1.0

See [`post_1.0/`](post_1.0/). It contains:

- the approved Interactions domain and Studio design;
- configurable canvas picking granularity;
- lazy structure sources and partial materialization;
- multiview synchronization;
- advanced annotation, representation, and chemical-metadata work;
- typing-generation and test-output studies;
- deeper large-system rendering analysis.

These remain useful, but they expand product scope or require benchmark and
upstream decisions. They do not block the current release.

## Practical decision

- **Done:** the router inventory/AnyWidget seam and the array-native serializer,
  negotiated buffer delivery, chunking, acknowledgement, cancellation, JSON
  fallback, and embedded-canvas E2E are implemented.
- **Now:** finish R2's canonical popup snapshot, then close D3 timeout/memory
  evidence, then implement D4 binary canvas-popup parity. Continue dogfooding
  and real-window Qt validation in parallel.
- **Preserve 1.0 semantics:** all selected structures remain materialized in
  `view.molsys`; binary is a transport choice, not a new scientific model.
- **Session lifecycle:** kernel restart or widget reconstruction creates a new
  attachment. Old popups are closed or disconnected and never adopt a new
  `session_id` implicitly; a replacement popup authenticates and bootstraps
  from current state.
- **First after 1.0:** implement the Interactions domain by vertical slices,
  with state/history/API before Studio UI.
- **Opportunistic small work:** configurable canvas picking may be scheduled
  independently once the post-1.0 API freeze opens.
- **Wait for dependencies:** chemical metadata waits for MolSysMT's schema;
  advanced MVS annotations and rendering tiers wait for their Mol*/product
  trigger.

## Triage rules

- `approved` means the design may be implemented; it does not make it a release
  gate.
- A proposal that depends on a benchmark records the benchmark command and
  fixture before implementation.
- Performance reports separate both structural axes: atom count and structure
  count.
- Overlapping proposals name one canonical owner for each concern.
- Once implemented, remove the document from this directory.
- A UI companion cannot start before its Python domain, protocol, state, and
  history contracts exist.
- Post-1.0 location is a scope decision, not an implicit commitment to
  implement every document.
