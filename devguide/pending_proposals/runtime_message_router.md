# Runtime router for Python, widget host, canvas, and popup

**Status:** active pre-1.0 foundation. R0, R1, and the R2 popup-envelope/control
slice are implemented. Popup molecular/high-frequency replay is compacted, but
the canonical popup scene projection (the R2 remainder) is still open. Qt parity
and data-plane endpoint routing remain pending.

**Scope:** identity, authority, routing, deduplication, acknowledgements, and
lifecycle across Python, AnyWidget/Qt host adapters, embedded canvases, and
popup canvases or panels. It does not define structural-array encoding or
scientific residency.

## Why the current path needs a contract

The current popup path:

- creates a second `MolSysViewerController`;
- replays the host `commandLog`;
- sends ad hoc `molsysviewer-*` messages through `postMessage(..., "*")`;
- sometimes applies an operation locally and then forwards it;
- identifies only `from: "host"` or `from: "popup"`;
- has no viewer/session/endpoint identity or duplicate-command guard;
- can clone complete molecular payloads into every popup replay.

Current message inventory:

| Legacy message | Current meaning | Target class |
|---|---|---|
| `molsysviewer-pop-ready`, `molsysviewer-panel-ready` | endpoint readiness | event |
| `molsysviewer-initial-sync` | host state replay | projection |
| `molsysviewer-sync-ui`, `molsysviewer-sync-autohide` | UI state | projection |
| `molsysviewer-popup-interaction` | user intent forwarded to Python | command/event by payload |
| `molsysviewer-sync-camera` | ephemeral camera synchronization | targeted event |
| `molsysviewer-log-from-popout` | diagnostics | event |
| `molsysviewer-sync-op` | projection host-to-popup, but command popup-to-host | ambiguous; replace |

The last row is the central defect in the legacy vocabulary: direction is
inferred from which window sent the message rather than represented in the
message itself.

This works for one viewer and modest payloads, but it does not establish who is
authoritative, prevent cross-talk between viewers, or bound data duplication.
The same logical protocol must also cross AnyWidget and Qt without forking scene
semantics.

## Authority model

Python is the only authority for reproducible scene mutations.

- A UI endpoint emits a **command** once.
- Python validates it and calls the public API.
- Python emits resulting **projections** to rendering endpoints.
- Endpoints apply projections; they do not independently commit reproducible
  state.
- Ephemeral camera motion, hover, diagnostics, readiness, and transport demand
  are explicit **runtime events**, not scene history.
- One accepted user command creates at most one Python history checkpoint.

Local visual feedback is allowed only when it is either ephemeral or an
optimistic projection with explicit reconciliation. The first implementation
does not require optimistic mutation.

## Endpoint model

Roles are explicit:

- `python`: scientific and reproducible scene authority;
- `widget-host`: AnyWidget browser adapter and embedded UI host;
- `qt-host`: standalone connector;
- `canvas`: one Mol* rendering endpoint;
- `panel-popup`: UI-only popup without its own canvas;
- `canvas-popup`: popup with its own Mol* controller.

Every instance has:

- stable `viewer_id` for one Python `MolSysView`;
- ephemeral `session_id` for one live attachment;
- unique `endpoint_id` per host, canvas, or popup;
- declared role and capabilities.

Two viewers in one notebook never share IDs or message acceptance state.

### Session lifecycle and reconnection

`session_id` is immutable for the lifetime of one live attachment. It is not a
presence value that an existing popup follows when a trait changes. A kernel
restart, widget reconstruction, or new frontend attachment creates a new
session and invalidates the old one.

Consequently:

- an endpoint accepts messages only from the session used in its authenticated
  handshake;
- a popup from an old session must reject messages from the replacement
  session, even when they originate from the same notebook tab;
- widget disposal closes its popups and revokes their endpoint registrations;
- if disposal cannot close an orphaned popup, that popup enters a visible
  disconnected state and cannot mutate or receive the new scene;
- the replacement host opens or bootstraps a popup with a fresh token,
  endpoint identity, and canonical scene snapshot;
- preserving the same physical popup window would require an explicit
  authenticated `rebind` handshake. No implicit `session_id` adoption is
  allowed pre-1.0.

Rejecting the new session in an old popup is therefore correct isolation, not a
delivery failure. Reconnection means establishing a new attachment and
reprojecting current state.

## Envelope

```typescript
type RuntimeDirection =
    | "command"
    | "projection"
    | "event"
    | "request"
    | "ack"
    | "error";

interface RuntimeEnvelope<T> {
    protocolVersion: 1;
    viewerId: string;
    sessionId: string;
    endpointId: string;
    targetEndpointId?: string;
    messageId: string;
    correlationId?: string;
    generation?: number;
    direction: RuntimeDirection;
    action: string;
    payload: T;
}
```

The envelope wraps existing `ViewerMessage` projections initially. It does not
require renaming every scene `op` in the first slice.

Validation:

- exact protocol version;
- matching viewer and session;
- registered source endpoint and allowed direction for its role;
- non-empty message and action IDs;
- bounded payload size for the control plane;
- generation where the action is generation-sensitive;
- action-specific payload validation before dispatch.

Malformed input produces a correlated error when possible. It never reaches a
controller as `any`.

## Dispatcher rules

- Maintain a bounded TTL/LRU set of processed `messageId` values.
- Duplicate commands return the prior acknowledgement and are not re-applied.
- Projections may fan out to all canvas endpoints or target one endpoint.
- Requests and responses preserve `correlationId`.
- Endpoint-local events are not broadcast unless their action contract says so.
- Closing an endpoint cancels its pending correlations and data requests.
- Reconnecting creates a new session or endpoint identity and receives a fresh
  state projection. The old endpoint never changes session in place and its
  messages remain stale.
- Routing failures and rejected messages are observable through diagnostics.

## Popup handshake and browser security

The host creates an unguessable handshake token and passes it to the popup at
creation. The popup must prove:

- `window.opener` is the expected source;
- token, viewer, session, and endpoint IDs match;
- protocol and capabilities are compatible.

After handshake:

- prefer the exact known `targetOrigin`;
- where blob/file/opaque origins prevent a useful origin string, validate
  `event.source`, the unguessable token, and all identity fields;
- never accept a message solely because its `type` starts with
  `molsysviewer-`;
- revoke tokens and remove listeners on close.

`BroadcastChannel` is not part of the pre-1.0 requirement. It remains a
post-1.0 transport experiment because origin isolation and structured-clone
cost vary across JupyterLab, VS Code, docs, and standalone contexts.

## Popup state and large data

Opening a popup must not replay an unbounded raw command log.

The bootstrap sequence is:

1. register endpoint and negotiate capabilities;
2. send a compact current scene/state projection;
3. send topology/static render state;
4. send the current materialized structures projection through that endpoint's
   selected connector capability;
5. acknowledge readiness after the scene is renderable.

A panel-only popup receives UI projections but no molecular buffers. A
canvas-popup receives one current molecular projection. Large data chunks are
referenced by generation and never stored repeatedly in scene history.

## Connector adapters

The core dispatcher is pure TypeScript/Python logic; transports only carry
envelopes:

- AnyWidget `model.send` / `msg:custom`;
- Qt live bridge and URL-scheme return events;
- `window.postMessage` for host-popup;
- docs/export adapters where applicable.

Transport-specific readiness and acknowledgements map into common envelope
actions. A connector cannot invent different mutation semantics.

## Implementation slices

### R0. Inventory and pure dispatcher

- classify every existing host/popup message as command, projection, event,
  request, ack, or error;
- implement typed envelope validation and a pure dispatcher;
- test two viewers, duplicates, stale sessions, malformed input, targeted
  fanout, and endpoint close;
- preserve existing transports.

Implemented in `js/src/messages/runtime-router.ts`, with typed validation,
endpoint registration, viewer/session rejection, targeted fanout, bounded
command deduplication, and endpoint removal covered by unit tests.

### R1. AnyWidget host and embedded canvas

- wrap model events and `ViewerMessage` delivery;
- route all reproducible UI actions to Python once;
- preserve runtime-only camera/hover paths;
- assert one command, one public-API mutation, one history step.

Implemented. A shared manifest `molsysviewer/runtime_actions.json` classifies
every browser-originated action (command/event/request/ack/error), with
Python-only `outbound_requests`, and `raw`/`data_plane` groups excluded from
enveloping in both directions. Both sides load the one file: Python through
`molsysviewer/runtime_contract.py` (stateless: manifest + `wrap_outbound`) and
`molsysviewer/viewer/runtime_router.py` (`WidgetRuntimeRouter`, the inbound
authority with bounded per-session command deduplication); TypeScript through
`js/src/messages/runtime-actions.ts` and `widget-envelope.ts`.

Python is the sole authority; the widget host is a single 1:1 endpoint and does
not run a browser-side router (unlike the popup topology). The envelope wrapping
lives in `MolSysViewerWidget.send` — the connector owns its wire format — so Qt
and other transports stay raw, `initial_messages` and `_message_history` keep
domain messages, and tests that replace `view.widget.send` observe the domain
message. `MolSysView._send_widget_message` is the single outbound chokepoint;
`_handle_inbound_message` validates identity, direction, and action↔payload
coherence, deduplicates commands (a duplicate yields an observable
`command_duplicate_ack` and is not re-applied), and unwraps to exactly the
domain `content` the handler received before. The `widget.py` bootstrap source
request stays raw because it runs before the adapter exists; binary buffers stay
on the data plane. Validated: full Python suite `1009 passed / 3 skipped`
(receptor), `255` JS, `tsc` `0`, `build:runtime`, and the array-native and
popup-channel E2E without skips; dedup, session, action↔payload coherence, and
the three outbound/inbound guards are mutation-verified.

### R2. Popup migration

- replace ad hoc `from` routing with endpoint handshake and dispatcher;
- remove local-plus-forward double application;
- bootstrap from current state rather than raw unbounded command history;
- test close, reopen, stale popup, two viewers, panel-only, and canvas-popup.

Implemented for the control plane. Every popup opening receives a fresh channel
containing the shared Python `viewer_id`/`session_id`, explicit
authority/host/popup endpoint IDs, mode, and an unguessable token. Both
directions validate the exact `event.source`, complete channel identity, source
endpoint, target endpoint, and `RuntimeEnvelope`. Same-origin popups use an
exact target origin. Duplicate popup commands are rejected by the shared
router. Popup runtime controls emit one intent and wait for the host projection
instead of mutating locally and then asking the host to repeat the mutation.

The former raw `commandLog` is replaced by `PopupReplayLog`. It retains only
the current molecular generation, coalesces current-state/high-frequency
projections, and supplies panel popups from an explicit UI-only allowlist.
Panel bootstrap therefore contains no topology, coordinates, or visual
operations that require a molecular structure. Canvas bootstrap still uses one
current JSON molecular projection until D4 adds binary endpoint delivery.

This is a bounded-data safety step, not yet the final canonical scene
projection. Non-reducible scene operations still form a replay journal and can
grow during a very long session. Closing R2 therefore still requires replacing
that journal with a Python/controller-derived current scene projection whose
size depends on current scene content, not interaction history.

Control-plane close/dispose revokes the channel, reopening creates a fresh
token, and widget disposal closes both canvas and panel popups.
`popup-channel.e2e.ts` covers an authenticated envelope round trip through the
real browser `postMessage` seam. Cancelling data-plane requests owned by a
closing popup remains part of D4 because popup data-plane delivery does not yet
exist.

Kernel restart/widget reconstruction is an explicit R2 lifecycle criterion:
the old popup must be closed or visibly disconnected, must reject the new
session, and must not receive or originate mutations for the replacement
viewer. A newly opened popup must authenticate under the new session and
bootstrap from the canonical snapshot. R2 does not add implicit popup rebind.

#### R2 canonical snapshot — approved design (in implementation)

The remaining R2 work replaces the `PopupReplayLog` journal with a
Python-originated **current-scene projector**. Approved decisions:

- `request_popup_scene_snapshot` is a browser->Python `request` carrying a
  `correlationId`, mode (`canvas`/`panel`) and the requesting `popupEndpointId`.
- The response is a correlated `projection`, targeted at the widget host, which
  routes it to the authenticated popup endpoint.
- A dedicated projector builds `ViewerMessage`s from **live state**, reusing the
  current records behind `export_state()` v2 plus the runtime state it omits
  (molecular system, visibility, frame, camera, scene look). It must not call
  `import_state()`, must not scan `_message_history`, and must not produce
  history. Size depends on current scene content, not interaction count.
- The current molecular projection is referenced through
  `_current_molecular_projection` ("current molecular state"), updated on every
  load/rebuild, never located by scanning the journal. Canvas receives one JSON
  molecular generation until D4 swaps it for typed buffers.
- Camera is taken from the host/controller as ephemeral endpoint state, never
  from Python's reproducible snapshot.

**Canvas snapshot order:** (1) reference to the current molecular projection;
(2) scene look — background, fog, lighting, clipping, legend, focus fade,
trajectory plot; (3) whole as *separate* representation/preset/params, colour
scheme, and visibility ops (not one op); (4) user layers before their members;
(5) regions in topological/`order` order — `create_region` with current indices
(including dynamic regions at the current frame), representation, order + layer
membership, visibility; (6) shapes/annotations/measurements from live records
via the projector; (7) consolidated `set_sections`; (8) object and layer
visibility after their members exist; (9) resolved colours after components
exist; (10) saved selections and active selection; (11) measurement settings;
(12) full `update_visibility`; (13) current frame and playback; (14) camera last,
from the host as ephemeral state.

**Panel snapshot:** the current-state summaries plus saved selections, active
selection, measurement settings, history state, addon runtime summary/context,
and current workspace/panel — and no molecular data. Ephemeral host-local UI
(camera, open panel, scroll) travels in a separate `endpointState` section so
Python does not become the authority for transient UI.

`PopupReplayLog` stays as temporary compatibility until the projector is
validated, then is removed. D4 replaces only the JSON molecular delivery with
typed buffers.

**Size invariant test:** N vs 100k interactions producing the same scene must
yield the same operation count, size within a fixed margin, and the same
normalized semantic content — ignoring legitimately monotonic counters
(`visibility_version`, generation, transport ids). A mutation that builds the
snapshot from `_message_history` must inflate ops/size and fail the test.

**Fidelity tests:** a dynamic region at the current frame; a dynamic shape;
hidden objects inside a hidden layer; `inherit` representation; overlapping
colours and order; a saved selection; box-absent and time-absent systems; and a
real Mol* tree after bootstrap.

#### R2 projector — implemented (Python side)

`MolSysView.build_popup_scene_snapshot(mode, endpoint)` lives in
`molsysviewer/viewer/popup_snapshot.py` (`PopupSnapshotMixin`). Guarantees are
mutation-verified in `tests/test_popup_snapshot.py` (purity, invariance,
isolation) and `tests/test_popup_snapshot_fidelity.py` (the eight fidelity
cases): it never calls `_send`, never mutates state or creates checkpoints,
never reads `_message_history` or `_build_export_messages()`, validates `mode`
strictly, copies defensively, and treats `endpoint` as correlation metadata
only. Inflating `_message_history` with 10,000 ops leaves the snapshot
byte-for-byte identical.

Protocol findings that changed the approved inventory, each verified against the
code rather than assumed:

- **Whole is two ops, not three.** No whole-colour op exists in the protocol
  (`set_whole_representation`, `show_whole`, `hide_whole` are the whole ops on
  both sides). Whole colour lives in `_atom_color_layers["whole"]` and reaches
  the frontend through the resolved `set_atom_colors`. Adding a third op would
  mean inventing protocol.
- **Saved selections travel verbatim.** `selections.records()` already returns
  complete `save_selection` messages, so they are emitted unchanged. (An earlier
  draft wrapped them in an invented `add_saved_selection` op; the dict spread
  silently overwrote it, so the emitted output was accidentally correct. The
  invented name is gone.)
- **Layer membership is not a separate op.** It already travels in the creation
  message's `options.layer_tag`; `_with_export_layer_tag` stamps the *current*
  membership onto each creation record. A separate `set_layer_tag` would be
  noise, since `layer_tag` defaults to the object's own tag.
- **Region order stays embedded** in `create_region`, which already carries it;
  a separate `set_region_order` would be redundant.
- **Hidden scene objects hide through `hide_layer`** with their `kind`, like
  layers. Omitting this was a real fidelity defect: a hidden shape reappeared in
  the popup. Emitted after creation, before colours.
- **Playback separates state from action:** the current `fps`/`mode`/
  `direction`/`step` are always projected; the play action only when playback is
  actually running.
- **Panel adds** `set_history_state`, the addon runtime summary, and the current
  workspace (from the last known panel-mode state). Addon *context items* are
  not projected yet: the only builder also sends, which would break purity — it
  needs a pure builder extracted first. Ephemeral host UI (camera, open panel,
  scroll) is deliberately absent; the host assembles it as `endpointState`.

#### Hot-path review of the envelope (measured, 2026-07)

Enveloping every message adds constant identity to each one, so the seam was
measured rather than tuned by intuition.

- `messageId` through `uuid4` cost ~4.4 µs versus ~0.35 µs for a counter (~12x).
  Both Python paths now use a per-session counter, like TypeScript already did;
  ids only need session uniqueness and the session id is part of the id.
- The envelope inflates a typical hover from 83 B to 458 B (5.5x, +375 B).
  At 60 messages per second that is ~22 KB/s. A second, compact wire format for
  ephemeral events was **rejected**: it would add dual-shape validation on both
  sides for a saving that small.
- The real hot-path cost was not the bytes but the message count. Mol\* re-emits
  hover on every resolved pick, rate-limited by `maxFps` and **not** suppressed
  by `prevLoci` (it stores the previous loci but never compares it). A mouse
  resting on one atom therefore sent ~30 identical messages per second to
  Python. The host now deduplicates the Python-bound hover projection by its
  normalized payload; local UI still receives every tick, and "the hovered thing
  changed" is the semantic a hover callback expects. This removes most hot-path
  traffic outright instead of shrinking it.

#### R2 wiring — implemented (request/response across the seam)

The popup bootstrap now asks Python for the canonical projection instead of
replaying the journal:

1. the popup emits `molsysviewer-pop-ready` / `molsysviewer-panel-ready`;
2. the host sends `request_popup_scene_snapshot` (a manifest `request`) carrying
   the mode and the requesting `popup_endpoint_id`, and keeps the envelope
   `messageId` as the pending correlation;
3. `MolSysView._handle_inbound_message` serves it before the domain handler —
   it needs the envelope to correlate — through `_answer_popup_scene_snapshot`,
   which replies with `WidgetRuntimeRouter.correlated_projection(...)`: a
   `projection` targeted at the widget host, carrying `correlationId`, the mode,
   the requested `popup_endpoint_id`, and the snapshot messages;
4. the host consumes that answer **at the seam** (it never reaches the
   controller), resolves the pending request, and sends
   `molsysviewer-initial-sync` with the canonical `messages`;
5. the host-local fields already travelling in that sync (camera, spin/swing,
   dark mode, autohide, viewer/controls/panel mode, ambient/split) are the
   `endpointState`: assembled by the host, never by Python.

`PopupReplayLog` remains only as the fallback when Python does not answer within
5 s, so a lost response can never leave a popup blank. An invalid `mode` is
reported and answered with nothing rather than with a malformed projection.

Validated: full Python suite `1024 passed / 3 skipped` (receptor), `257` JS,
`tsc` `0`, `build:runtime` with R2 confirmed in the bundle, and the
popup-channel and array-native E2E without skips.

#### D4a implemented: endpoint-targeted delivery

`PopupHostManager.send` fans out to every open popup. That is right for shared
scene projections and wrong for anything endpoint-specific — and the R2 popup
bootstrap was using it. **With a canvas popup and a panel popup open at the same
time, the canvas bootstrap (which carries the molecular projection) was also
delivered to the panel popup**, defeating the "a panel popup receives no
molecular data" rule at the delivery layer even though the snapshot itself was
correctly built per mode.

`sendTo(mode, type, data)` now delivers to exactly one endpoint and reports
false when it is not open; both bootstrap paths use it. `send` remains the
deliberate fan-out. Mutation-verified: restoring the broadcast fails the
isolation test.

Closing a popup also cancels the work the host owns for it. `PopupHostOptions`
gained `onEndpointClosed`, fired from every close path (the polling detector and
the explicit `close`), and the host settles that endpoint's pending
scene-snapshot requests instead of leaving them until their timeout.

Still open for D4b: delivering the canvas popup a **typed** molecular generation
(Python re-streams to the popup endpoint, the host relays chunk by chunk with
buffer transfer and retains nothing), which then allows lifting the
`enable_popout` restriction that currently disables the binary path whenever a
popout is possible. Qt keeps the JSON path and needs its own benchmark.

### R3. Qt parity

- map Qt readiness, delivery acknowledgement, and errors to the same envelope;
- retain Qt's bounded retry policy;
- verify that Qt does not fork Python or controller semantics.

### R4. Data-plane delivery

- route structure-data descriptors and chunks by endpoint;
- keep binary buffers outside command/history logs;
- enforce cancellation when popups or views close.

## Tests and mutation targets

Unit tests must exercise the dispatcher without a browser. Real browser E2E
must cover the actual `postMessage` seam.

Required cases:

- two viewers cannot cross-receive;
- duplicate command produces one Python mutation/history step;
- popup command is not applied locally before its projection;
- stale popup after reopen is rejected;
- kernel restart/widget reconstruction leaves the old popup closed or
  disconnected and unable to adopt the new session;
- a popup opened by the replacement widget authenticates with the new session
  and receives a fresh canonical snapshot;
- malformed or unregistered source is rejected observably;
- panel popup receives no molecular data;
- canvas popup receives only the current generation;
- closing popup cancels pending requests and removes listeners;
- camera events do not enter scene history;
- popup bootstrap does not accumulate superseded molecular payloads.

Guards that prevent cross-talk, duplicate application, stale delivery, or
unauthorized routing require mutation checks.

## Acceptance criteria

- one authority and one history checkpoint per accepted mutation;
- typed validation at every connector boundary;
- no `postMessage("*")` unless an opaque-origin path is paired with source,
  token, viewer, session, and endpoint validation;
- no raw all-history replay for popup bootstrap;
- no cross-talk with two viewers and multiple popups;
- reconnect, kernel-restart, close, error, and stale-message behavior are
  deterministic;
- no endpoint adopts a replacement `session_id` without a new authenticated
  handshake;
- Jupyter, Qt, embedded canvas, and popup share routing semantics;
- state v2 and HTML export remain independent of transient envelopes.

## Explicitly post-1.0

- `BroadcastChannel` optimization;
- multiple synchronized viewports in one canvas;
- remote collaboration or multi-user authority;
- optimistic distributed mutations;
- camera/movie product expansion.
