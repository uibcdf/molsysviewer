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
| Browser stream assembly and latest accepted generation | one `ArrayNativeStreamReceiver` per rendering endpoint | viewer controller / popup runtime | endpoint runtime |
| Authenticated popup endpoint identity and targeted browser delivery | popup host/router | popup windows | authenticated endpoint close |
| Qt ordered message queue, in-flight entry and payload references | `QtMessageBridge` | `QtViewChannel` | Qt bridge generation / window close |

## Consequences

- `core.py` orchestrates manager results but never writes transfer state or a
  terminal `TransferState` directly.
- Endpoint lifecycle fields do not live in parallel dictionaries. Registering,
  deferring and closing act on one endpoint bundle.
- Completing or falling back a popup generation releases its retained payload
  but does not delete its manager. The receiver retains its latest generation,
  so the sender's counter must survive until endpoint close.
- Static export has no independent journal or projector. `ExportMixin` is an
  entrypoint only; the canonical constructor lives in `popup_snapshot.py`.
- Qt deliberately does not share the AnyWidget transfer manager. Its ordered
  queue and payload-reference scheme satisfy S8 at a different connector seam.

## Structural guards

`tests/test_structure_transfer.py` prevents transfer-state transitions from
returning to `core.py`. `tests/test_transport_ownership.py` prevents the former
parallel endpoint dictionaries from returning, proves endpoint-close isolation,
and asserts that the static snapshot constructor is defined exactly once.

General decomposition of `index.ts`, `viewer-controller.ts` or unrelated
frontend orchestration is not required before 1.0. It remains justified only by
a newly demonstrated duplicate mutable owner, not by file size alone.
