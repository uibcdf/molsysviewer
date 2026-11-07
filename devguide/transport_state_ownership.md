# Transport and projection state ownership

**Status:** normative for the pre-1.0 runtime

This table records the single owner of mutable state introduced or materially
changed by transport phases 2 through 5. An owner controls lifetime and mutation;
callers may coordinate effects or consume projections without becoming another
authority.

| Mutable state | Sole owner | Coordinators / readers | Lifetime boundary |
|---|---|---|---|
| One molecular transfer's state, identity, chunks, retained payload and deadline | `StructureTransfer` | `StructureTransferManager` | terminal transition releases once |
| Generation allocation and active transfer for one destination | `StructureTransferManager` | `MolSysView` sends requested effects | endpoint lifetime; manager persists inactive between generations |
| Endpoint mode, transfer manager, deferred scene queue and flush reentrancy | `EndpointTransferRegistry` / `EndpointTransferState` | `MolSysView` transport chokepoints | popup close or view close; embedded bundle lasts for the view |
| Current lazy molecular projection and revision | `MolSysView` scene state, updated through `HistoryMixin` send paths and scene reset | data plane and canonical projectors | current loaded/rebuilt molecular system |
| Canonical canvas, panel, embedded and static projection algorithms | `PopupSnapshotMixin` | popup request, ready and `ExportMixin` | pure result per request; no retained snapshot copy |
| Static-export entrypoint | `ExportMixin` delegates to `PopupSnapshotMixin._build_static_export_snapshot` | HTML/export consumers | one projection build |
| Widget envelope identity and command deduplication | `WidgetRuntimeRouter` | AnyWidget connector and `MolSysView` inbound seam | widget session |
| Remote endpoint registration, placement capabilities and accepted-command deduplication | one `SessionRuntimeRouter` | authenticated remote connectors and Python authority | immutable remote viewer session |
| Remote control/data-plane separation and connector callbacks | one `RemoteViewChannel` | `MolSysView` transport seam and future session service | remote connector close |
| Chromium child process, ephemeral profile, diagnostic channel and bounded restart allowance | one `ManagedRenderWorker` | future session service / worker health projection | render-worker attachment |
| Browser stream assembly and latest accepted generation | one `ArrayNativeStreamReceiver` per rendering endpoint | viewer controller / popup runtime | endpoint runtime |
| Authenticated popup endpoint identity and targeted browser delivery | popup host/router | popup windows | authenticated endpoint close |
| Correlated visual capture tickets, reply ownership and deadlines | one `FrontendRequests` per View | Python async saves and Studio save owner | reply, cancellation, timeout, endpoint or View close |
| Pending Studio work-file intentions and bounded completed IDs | one `WorkFileSaves` per View | authenticated Studio requester / existing atomic writers | capture verdict or writer completion; View close cancels captures |
| Capture deadline scheduling and callback lifetime | existing widget host loop or Qt GUI channel | `WorkFileSaves` | fired/cancelled callback or connector close; no timer worker thread |
| Qt ordered message queue, in-flight entry and payload references | `QtMessageBridge` | `QtViewChannel` | Qt bridge generation / window close |

## Consequences

- `core.py` orchestrates manager results but never writes transfer state or a
  terminal `TransferState` directly.
- Endpoint lifecycle fields do not live in parallel dictionaries. Registering,
  deferring and closing act on one endpoint bundle.
- Completing or falling back a popup generation releases its retained payload
  but does not delete its manager. The receiver retains its latest generation,
  so the sender's counter must survive until endpoint close.
- Scene commands and runtime projections go through each destination's own
  deferred queue. The primary copy is explicitly addressed when popups exist;
  the host must not apply it and later broadcast another copy. That late fanout
  can deliver `clear_all` after a faster popup has already loaded the replacement
  structure. JSON molecular fallback is also addressed once per canvas.
- The widget relays explicitly addressed domain commands through the popup's
  ordered operation queue; only structural-stream protocol messages and the
  JSON molecular load use the structure-data path. An explicitly host-addressed
  message stays at the host. Legacy unaddressed browser messages retain their
  existing fanout behavior.
- Add-on widget mounting/state is local to its panel owner. The AnyWidget seam
  explicitly targets its host for primary-local messages, including subsequent
  widget state sends. Qt and Remote retain their connector-owned primary
  default; a widget-host endpoint must not be invented for those connectors.
  A popup JSON fallback also uses its own deferred queue, never the primary's.
- Studio verdicts and their diagnostics are requester-owned control traffic,
  not scene projections. They bypass structural-stream gates and never unlock
  another window's controls, including when request IDs coincide. Capture
  barriers instead follow the originating canvas's structure/scene work.
- Kernel continuations run after the outer molecular guard releases, including
  failure, cancellation, expiration and public close. Local registry-lock
  release alone does not guarantee that the connector released its outer guard.
- Static export has no independent journal or projector. `ExportMixin` is an
  entrypoint only; the canonical constructor lives in `popup_snapshot.py`.
- Qt deliberately does not share the AnyWidget transfer manager. Its ordered
  queue and payload-reference scheme satisfy S8 at a different connector seam.
- A remote connector does not turn `MolSysView` into a network server.
  `SessionRuntimeRouter` owns remote identities, placement and deduplication;
  `RemoteViewChannel` adapts only accepted domain messages at the existing
  transport seam and keeps binary/data-plane traffic outside envelopes.
- `ManagedRenderWorker` is the sole owner of its child process and temporary
  browser profile. DevTools is bound to loopback and is only a private health
  channel; it never becomes a client protocol or another scene authority.

## Structural guards

`tests/test_structure_transfer.py` prevents transfer-state transitions from
returning to `core.py`. `tests/test_transport_ownership.py` prevents the former
parallel endpoint dictionaries from returning, proves endpoint-close isolation,
asserts that the static snapshot constructor is defined exactly once, and checks
independent scene ordering when the popup's stream completes before the primary.
The registered Studio browser guard additionally receives real session restores
and source/popup operations; a Python transport assertion cannot substitute for
actual rendered acceptance. `tests/test_live_state_capture.py` protects failure
notification outside nested molecular guards.

General decomposition of `index.ts`, `viewer-controller.ts` or unrelated
frontend orchestration is not required before 1.0. It remains justified only by
a newly demonstrated duplicate mutable owner, not by file size alone.
