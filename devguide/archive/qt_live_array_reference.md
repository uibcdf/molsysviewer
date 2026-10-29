---
summary: Qt live loading bypasses its declared array-native molecular path
issue: uibcdf/molsysviewer#275
status: resolved
opened: 2026-10-29
closed: 2026-10-29
severity: medium
verification: reproduced
area: [standalone, transport]
guard: tests/test_qt_transport_contract.py::test_a_canonical_live_load_uses_numeric_scheme_bytes_without_json
normative:
blocked_by: []
supersedes: []
---

# Qt live loading falls back to coordinate JSON unconditionally

**Reported:** final standalone source review, 2026-10-29.

## What

With `MOLSYSVIEWER_QT_PAYLOAD_REF_THRESHOLD=1`, a real Qt window reaches Ready
and serves a molecular reference, but its lazy canonical molecular projection
is materialized as numeric JSON and no binary payload is owned. This contradicts
the D4 Qt array-native completion claim in `data_plane_architecture.md`.

## How

The old conversion reads an unset `bridge.view` attribute after constructing
numeric JSON. An isolated test supplied that attribute manually, missing the
actual host path and even permitting a raw message to be replaced by another
system's data. The correction negotiates reference capability version 1 and
passes only the current canonical lazy projection to a private Qt adapter.
The existing array serializer supplies topology, coordinates, boxes and time.
The scheme handler owns its binary bytes and generation lifetime. Structure
delivery waits for `structure_ready`, including the array-reference operation.

## Why

Large structures should use the declared transport without creating nested
coordinate JSON first. Raw messages must preserve their own payload identity.
This avoids an unnecessary serialization, not all copies or all RAM growth.

## What was refuted

Simply binding `bridge.view` would leave numeric JSON construction in place
and could substitute unrelated molecular data for a caller's raw message.
AnyWidget's binary buffers cannot be passed through the JSON-only Qt channel;
the existing scheme-reference mechanism is the correct owner.

## Resolution

The negotiated private Qt adapter now receives the current lazy projection
before coordinate JSON exists. The real live-channel guard checks capability
fallback, unchanged raw payloads, generation cleanup and binary coordinates,
box and time for structures [8, 0, 3]. Forty-three related Python contracts
pass. The native workbench guard passes on the Linux desktop/GPU and explicit
X11/SwiftShader, requiring unmaterialized initial and ten replacement
projections, actual served payloads, changing molecular pixels and both hosts.
All 332 JS unit tests pass. The data-plane contract records this correction to
the earlier live-host parity claim and the raw-byte threshold distinction.
No out-of-core loading, universal RAM bound, published artifact or new platform
certification is inferred.
