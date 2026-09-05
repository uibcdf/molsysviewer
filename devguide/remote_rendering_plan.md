# Remote rendering and session-host plan

**Status:** accepted pre-1.0 direction; evaluation complete; RRS0 and RRS1
completed; RRS2 server-rendered browser workflow validated end to end, including
upload, export and reconnect.

**Decision date:** 2026-09-01.

**Scope:** let one MolSysViewer session run on a workstation, server or cluster
node while a browser or the native Qt shell provides the interactive client.
This is rendering placement, not remote multi-user collaboration and not a
second scene/state model.

This plan extends [`standalone_host_plan.md`](standalone_host_plan.md), preserves
[`runtime_message_router.md`](runtime_message_router.md), and preserves the data
ownership contracts in [`data_plane_architecture.md`](data_plane_architecture.md)
and [`transport_state_ownership.md`](transport_state_ownership.md). If they
disagree, those normative contracts win until amended deliberately in the same
change.

---

## 1. Product decision

MolSysViewer exposes two explicit rendering placements:

```python
render_on="client"
render_on="server"
```

There is no `auto` mode. Resource probing may diagnose a choice, but must not
silently move scientific work or rendering between machines.

- `client`: Mol* and WebGL run in the browser or Qt WebEngine client. Python
  and reproducible session authority may still reside on a server.
- `server`: Mol* and WebGL run in a managed Chromium render worker. The client
  presents a video viewport and the shared workbench UI.

Both placements support both client shapes:

| Client | `render_on="client"` | `render_on="server"` |
|---|---|---|
| Browser | full browser runtime, client GPU | UI-only browser client plus remote video |
| Qt standalone | full embedded runtime, current native-window experience | same native shell, UI-only surface and remote video |

The user-facing terms are **client rendering** and **server rendering**.
Internal molecular “scene” terminology remains, but `scene` and `pixel` are not
rendering-mode names.

The existing local standalone remains valid. Its compatibility default is
`render_on="client"`; absence of a flag does not mean automatic placement.

## 2. Why this belongs in 1.0

Remote execution is already a real development and scientific workflow:
MolSysViewer may run on spika while the user works from aleph. Requiring a
remote GNOME desktop moves an entire desktop to reach one application and does
not establish reusable server architecture.

The server-rendered slice pays forward:

- it uses the existing Python authority and runtime envelope;
- it introduces the session gateway a future MolSys-AI actor will need;
- it changes rendering placement without changing public scene semantics;
- one server supports browser and preferred Qt shell;
- worker lifecycle and diagnostics extend naturally to clusters.

The 1.0 slice remains single-user and single-authority. It does not pull remote
collaboration into 1.0.

## 3. Evaluated facts

These measurements on spika on 2026-09-01 are feasibility evidence, not
permanent performance promises.

### 3.1 Headless render worker

- Chrome without a desktop reached the NVIDIA GeForce GTX 1080 through ANGLE
  OpenGL/EGL with `--use-gl=angle --use-angle=gl-egl`.
- WebGL2, GPU compositing and GPU rasterization were active. Default headless
  launch selected SwiftShader, so a successful launch is insufficient: the
  worker must report its actual renderer.
- Real Mol* loaded a structure, camera input changed the view, and synthetic
  DOM pointer events produced real picks with structure, residue and atom data.
- The current Mol* input observer does not reject events merely because
  `isTrusted` is false. A validated input adapter can use the real canvas path
  rather than inventing a second picking engine.

### 3.2 Video transport

- `canvas.captureStream()` and WebRTC delivered live frames.
- 1920x1080 at 30 fps succeeded after setting `contentHint="detail"`, 8 Mbit/s
  maximum bitrate, 30 fps maximum, `scaleResolutionDownBy=1` and
  `maintain-resolution` degradation preference.
- Without explicit policy Chromium silently reduced the stream to 640x360.
  Production must not trust WebRTC defaults for scientific detail.
- A three-second run encoded 92 frames and decoded 91; mean encode time was
  about 10.4 ms/frame, with no WebRTC quality limitation.
- Video encoding was software although Mol* rendering used the GPU. Hardware
  encoding is an optimization, not a 1.0 prerequisite.

### 3.3 Qt remote client

- The validated UIBCDF Qt stack was:

  ```text
  shiboken6-uibcdf             6.9.2  *_4
  pyside6-essentials-uibcdf    6.9.2  *_4
  pyside6-addons-uibcdf        6.9.2  *_6
  qt6-positioning-uibcdf       6.9.2  py313_1
  qt6-webengine-uibcdf         6.9.2  py313_2
  ```

- ICU data, the V8 snapshot, resources, locales and `QtWebEngineProcess` were
  present. The real Qt JavaScript-to-Python transport smoke passed.
- In a split-process probe Chrome produced video and Qt was only the receiver.
  Qt connected, held a live track, decoded VP8 at 640x360 and reached video
  `readyState=4`.
- A WebRTC data channel opened bidirectionally: Qt received a sequenced server
  message and the server received a sequenced pointer event from Qt.
- Qt `offscreen` decoded frames but could not present native graphics buffers
  (`Buffer Handle is null`). This artificial-platform limitation does not
  invalidate the windowed client. A visible xcb test on aleph remains an
  implementation acceptance item.
- This Qt build advertised VP8, VP9 and AV1 but not H.264. VP8 is the mandatory
  1.0 interoperability codec.

### 3.4 Cost and topology

- Measured Chrome launch was about 0.74 s, harness load 2.48 s and Mol* scene
  creation 2.04 s.
- One worker used approximately 210–275 MB maximum RSS; a representative run
  was about 213 MB.
- Spika (`192.168.0.101`) is reached from aleph through ixtlilton. HTTP and
  WebSocket traffic can use SSH forwarding, but the machines do not share a
  directly reachable ICE network; server rendering needs the tested TURN/TCP
  relay path or equivalent routed connectivity.
- `aiohttp` is present in the evaluated environment and can provide HTTP and
  WebSocket service. FastAPI, Uvicorn and aiortc are unnecessary. WebRTC stays
  browser-owned; Python handles authority, signaling and lifecycle.

## 4. Target architecture

```text
Browser or Qt client
  - native host shell where applicable
  - shared UI-only workbench surface
  - <video> viewport for server rendering
  - WebSocket control/signaling
  - WebRTC input data channel
                 |
                 v
Python session server
  - one authoritative MolSysView
  - authenticated session router
  - command validation and public-API dispatch
  - canonical projections and history
  - upload/download and worker lifecycle
                 |
                 v
Managed Chromium render worker
  - full MolSysViewerController and Mol*
  - structural and scene projections
  - server GPU, picking and ephemeral camera
  - WebRTC video sender and input receiver
```

For client rendering the worker is absent. The browser or Qt endpoint declares
the `canvas` capability and receives canonical molecular and scene projections.

For server rendering the client must not receive molecular coordinates merely
to operate its UI. Python sends structural/render projections to the worker;
the client receives workbench summaries, interaction results and video.

## 5. Authority and routing contracts

Python remains the only authority for reproducible mutations.

1. A client emits a semantic command once.
2. The session router authenticates viewer, session, endpoint and actor.
3. Python validates the action through the shared manifest and invokes the
   existing public API.
4. Python creates at most one history checkpoint for the accepted command.
5. Python emits canonical projections to the client UI and rendering endpoint.
6. Endpoints apply projections; they never commit reproducible state.

Server rendering must not add a scene journal or make the worker scientific
authority. Worker loss is renderer loss: a fresh worker receives current
authoritative state.

`WidgetRuntimeRouter` remains the AnyWidget connector. Remote sessions require
a session-level router with an endpoint registry; broadening a 1:1 widget
object into an implicit network server would mix lifetimes and ownership.

`QtViewChannel` establishes the connector interface used by `MolSysView`:
outgoing `send`, incoming `on_msg`, initial-message behavior and close. A
`RemoteViewChannel` implements that interface and delegates identity, delivery
and reconnection to the session router. It does not duplicate `MolSysView`.

## 6. Transport separation

### 6.1 Control and signaling

An authenticated WebSocket carries:

- WebRTC offer/answer and ICE signaling;
- runtime envelopes for semantic commands and projections;
- acknowledgements, errors, readiness and capability negotiation;
- worker/session lifecycle and reconnect instructions;
- low-rate host commands such as open, save and export.

These messages are ordered and reliable.

### 6.2 Structural and bulk data

- Client rendering sends array-native structure data to the rendering client
  under existing generation and ordering contracts.
- Server rendering sends structural arrays only to the local worker. The
  poor-GPU client avoids coordinate transfer and memory residency.
- Opening a local file in a remote browser or Qt client uploads it explicitly
  with progress, cancellation, size limits and a filename. A client path must
  never be mistaken for a server path.
- Export/save results return as bounded downloads. Qt uses native save dialogs;
  the browser uses normal downloads.

The worker transport reuses the array-native representation and generation
semantics. It may use binary WebSocket frames or authenticated loopback HTTP;
it must not regress to nested coordinate JSON.

### 6.3 Ephemeral interaction

A reliable ordered `RTCDataChannel` named `input` carries validated:

- pointer move/down/up/cancel and click sequence;
- wheel deltas, modifiers, buttons and relevant keys;
- viewport size, normalized coordinates and device-pixel ratio;
- monotonically increasing sequence and input timestamp.

Pointer motion is coalesced client-side. A later measurement may justify an
unordered/loss-tolerant motion channel, but 1.0 does not need two input
semantics before a real bottleneck exists.

The worker's `RemoteInputAdapter` validates bounds, rate and sequence, then
drives the real Mol* canvas path. Picking and interactions return through the
runtime router. Ephemeral camera motion stays outside history; snapshots needed
by export/persistence cross the authority boundary at explicit stable points.

## 7. Frontend decomposition

Current `isPanelOnly` is not a remote client: controller creation still creates
a canvas, initializes `PluginContext`, Mol* and WebGL before hiding the canvas.

The durable decomposition is:

- a **rendering surface** owning Mol*, canvas, picking and local camera;
- a **workbench surface** owning panels, toolbars, summaries and actions;
- a small **interaction port** for controls that currently call the local
  controller directly.

The interaction port has local and remote implementations. Existing panels
already use `onAction` and are largely ready. Canvas toolbar, trajectory
controls, hover tooltip and some context interactions need explicit decoupling.

The server-rendered client has a separate entrypoint that does not create Mol*
or WebGL. Avoiding initialization is required; excluding Mol* from that bundle
is also the intended size/startup outcome.

The remote viewport is a normal layout participant containing video,
status/error overlays and input surface—not a screenshot widget beside a
second panel system.

## 8. Qt client contract

The Qt remote client preserves standalone identity:

- same application window, icon, title and menus;
- native open/save/export dialogs;
- local shortcuts and window management;
- same workbench surface as the browser;
- no browser chrome;
- clear connecting, ready, degraded, disconnected and failed states.

Conceptually:

```bash
molsysviewer-qt --connect SESSION_URL
```

Native menu actions become authenticated session commands. A file selected on
aleph uploads explicitly; a server-side file opens through the server CLI or a
separately authorized server-path operation. A bare path never ambiguously
selects a filesystem.

## 9. Public server CLI and configuration

**Decision recorded 2026-09-02:** 1.0 will expose a public, foreground,
single-session server CLI. Its intended name is `molsysviewer-server`, which is
deliberately distinct from the local `molsysviewer` launcher and the
`molsysviewer-qt` client:

```bash
molsysviewer system.pdb
molsysviewer-server system.pdb --render-on client
molsysviewer-server system.pdb --render-on server
molsysviewer-qt --connect SESSION_URL
```

The server CLI is a thin adapter over the same programmatic session API used by
tests and applications. It must not become a second implementation of session
authority, routing, loading or worker lifecycle. The initial
`devtools/remote_session.py` launcher supplied its development seed. The public
entrypoint is now registered against `molsysviewer.remote.server_cli`; the
following contract defines its bounded surface.

### 9.1 Responsibilities in 1.0

For one process and one authoritative session, the public CLI owns:

- starting empty or loading one server-side molecular-system source;
- selecting explicit, immutable `--render-on client` or `--render-on server`;
- binding to loopback by default and accepting an explicit listen port;
- generating a per-session bearer credential and authenticated client URL;
- starting and supervising the managed render worker in server rendering;
- reporting renderer, WebGL and media diagnostics without leaking molecular
  payloads or credentials into ordinary diagnostic logs;
- printing actionable browser, Qt-client and SSH-forward connection guidance;
- remaining in the foreground and closing the session, endpoints and worker on
  `SIGINT`/`SIGTERM`;
- returning useful non-zero exit status for configuration, bind, load, GPU,
  worker and session-start failures;
- exposing only the bounded deployment configuration needed by the supported
  LAN/VPN/SSH and administratively prepared reverse-proxy paths: external URL,
  ICE servers, GPU policy and established upload/session limits.

TURN passwords are read through `--turn-credential-env`, never accepted as a
literal command-line argument. `--video-width`, `--video-height`,
`--video-fps` and `--video-max-bitrate` expose bounded server-rendering
parameters without making placement or quality implicit.

`--json` provides a versioned, single-line `session-ready` record for scheduler
and shell integration rather than making automation scrape human-oriented
output. It includes the selected placement, authenticated session URL, Qt
argument vector, SSH-forward parameters and bounded renderer diagnostics.

There is no resource-based automatic placement. A diagnostic may report GPU,
renderer and codecs and recommend a mode, but the user chooses it.

### 9.2 Explicit 1.0 limitations

`molsysviewer-server` is not a service manager. In 1.0 it intentionally does
not promise:

- background/daemon operation, process discovery or operating-system service
  installation;
- multiple authoritative sessions in one process or multi-user collaboration;
- durable sessions, restoration after Python-process loss or worker migration;
- user accounts, institutional identity, role-based access or shared links;
- automatic TLS certificates, reverse-proxy installation or managed TURN;
- universal Internet/NAT/firewall reachability;
- cluster job submission, queue monitoring, GPU allocation or worker pools;
- resource accounting, admission control, quotas or tenant isolation;
- adaptive codec/bitrate/resolution or automatic rendering placement;
- MolSys-AI startup, model placement or agent lifecycle.

One invocation owns one session and its lifetime. Stopping that process ends
the authoritative session. A path passed on spika names a spika filesystem
object; a file chosen in aleph is an authenticated upload. The CLI must never
blur those two permissions. The supported initial network remains loopback
plus SSH forwarding, direct LAN/VPN, or an explicitly administered proxy/ICE
deployment.

### 9.3 Post-1.0 service evolution

A future managed service may add a long-lived control plane around the stable
session API:

- create/list/stop multiple sessions and reconnect to durable session records;
- authenticate users and issue scoped, revocable client credentials;
- integrate TLS, reverse proxies and managed TURN;
- submit and monitor scheduler jobs and place workers on GPU pools;
- enforce resource limits, quotas, tenancy and audit/observability policy;
- migrate or recover workers without changing scientific authority;
- host MolSys-AI as another authenticated actor with explicit resource and
  cancellation ownership.

That layer may have its own administrator CLI and HTTP API. It should compose
`RemoteSessionService` rather than progressively turning
`molsysviewer-server` into a monolithic daemon. The 1.0 command can remain the
simple direct-server tool even after managed deployments exist.

## 10. Security baseline

- Bind to loopback by default; another interface is explicit.
- Generate an unguessable session token and validate it at handshake. Do not
  put reusable credentials in logs or exported state.
- Validate envelope identity, direction, action and endpoint capability at
  every connector boundary.
- Keep DevTools/debug endpoints on authenticated loopback; they are never the
  client protocol.
- Bound/rate-limit input, uploads, messages, sessions and worker resources.
- Treat client upload and server-path access as different permissions.
- Support HTTPS/WSS reverse proxies. Automatic certificates are post-1.0.
- Make ICE servers configurable in 1.0. Administered TURN is post-1.0.
- Start Chromium with its normal sandbox where supported. Evaluation used
  `--no-sandbox`; production must not silently default to it. An explicit
  override has a visible warning and only a documented contained deployment.
- Give worker pages restrictive CSP and no arbitrary navigation.

The initial supported network is direct LAN, VPN or an administratively
prepared path with ICE connectivity. “Every NAT and institutional firewall” is
not an honest 1.0 promise without TURN.

## 11. Failure and lifecycle

Every session has immutable identity and explicit endpoint capabilities.
Reconnect creates a fresh authenticated attachment and canonical projection;
it does not adopt a stale `session_id`.

The UI distinguishes:

- server unreachable or authentication rejected;
- worker starting;
- WebGL unavailable or unexpected software renderer;
- WebRTC negotiating or ICE failed;
- video stalled while control remains connected;
- worker crashed/restarting;
- authoritative Python session ended.

Worker restart:

1. revoke dead endpoint;
2. create worker with new endpoint identity;
3. perform capability/GPU health checks;
4. send topology/structures under a fresh generation;
5. send canonical scene projection after structural readiness;
6. establish new WebRTC attachment;
7. report ready only when renderable.

No unbounded replay is introduced. If Python authority is lost, a worker image
cannot reconstruct scientific state.

## 12. MolSys-AI compatibility

MolSys-AI is post-1.0, but 1.0 must not force it to bypass authority later.
Reserve metadata for:

- actor identity/kind (`human`, `agent`, `system`);
- request/correlation and causation identity;
- command provenance;
- cancellation and deadline identity;
- targeted result/error delivery.

The agent is another authenticated command origin. It calls the same public API
through the session gateway, receives the same projections and creates the same
history checkpoints. It does not manipulate worker DOM, mutate Mol* behind
Python or own parallel history.

The future chat panel is another workbench surface. Agent and rendering
locations are independent: MolSys-AI may run on the server with either
rendering placement.

## 13. Pre-1.0 implementation slices

### RRS0 — protocol and ownership contract

**Completed 2026-09-02.**

- Freeze session, endpoint and capability vocabulary.
- Add only backwards-compatible envelope fields needed by remote connectors
  and reserved AI provenance.
- Define `RemoteViewChannel`, session-router and worker ownership.
- Define input/signaling schemas and rejection behavior.

**Exit:** connector tests prove validation, deduplication, stale-session
rejection and one checkpoint per accepted command.

The shared manifests now freeze rendering placements, endpoint roles and
capabilities, signaling kinds and bounded input packets. Python and TypeScript
validate the same vocabulary. `SessionRuntimeRouter` owns the immutable remote
session and accepted-command deduplication; `RemoteViewChannel` provides the
transport-neutral `MolSysView` seam while keeping control and binary/data-plane
traffic separate. Tests cover both client shapes in both placements, actor and
session rejection, reserved agent provenance, duplicate acknowledgement and one
history checkpoint for one accepted command.

### RRS1 — managed render worker

**Completed 2026-09-02.** The managed process has explicit GPU policy,
Chromium discovery, an ephemeral profile, loopback-only private DevTools,
WebGL2/renderer/WebRTC diagnostics, normal-sandbox default, bounded shutdown,
crash detection and exactly one restart. The private HTTP/WebSocket host serves
a restrictive-CSP worker page, keeps its capability token in an `HttpOnly`
cookie rather than the URL, validates origin and exact worker registration, and
attaches that endpoint to `SessionRuntimeRouter`.

The canvas-only entrypoint waits for controller and registration readiness,
then sends raw readiness and receives canonical projections. Control messages
remain enveloped; array-native headers are followed by their original binary
WebSocket frames and retain the existing generation/ACK/backpressure contract.
Transport support is an explicit connector capability rather than an
`AnyWidget` type check, so the remote channel can negotiate buffers while the
Qt JSON control channel still refuses them. A render worker cannot originate
commands as the system actor; RRS2 must attribute interaction commands to the
authenticated browser/Qt client that supplied the input.

`RemoteInputAdapter` validates identity and monotonic sequence, maps normalized
coordinates to the live canvas, and dispatches through Mol*'s real
canvas/window input observer rather than a second picking path. Real spika GPU
tests prove camera motion and molecular picking through the adapter. The
permanent vertical guard loads the real pentalanine demo (62 atoms, 100
structures) through array-native into the managed NVIDIA GTX 1080 worker,
finishes with no active retained transfer and rejects software rendering.

- Launch Chrome/Chromium without a production Playwright dependency.
- Serve an internal worker entrypoint and connect the session router.
- Report WebGL2 renderer, GPU/SwiftShader and WebRTC capabilities.
- Load array-native payloads and canonical projections.
- Implement bounded shutdown, crash detection and one restart path.

**Exit:** a headless real-GPU test loads a real demo and renders/picks without
xvfb or Mesa fallback; unexpected software rendering fails visibly.

### RRS2 — session service and browser client

**Server-rendered vertical slice completed 2026-09-02.** `RemoteSessionService`
now composes the Python authority, authenticated session router and managed GPU
worker behind a single-user loopback HTTP/WebSocket surface. The bearer token
travels in the URL fragment only for initial exchange, becomes an `HttpOnly`,
`SameSite=Strict` cookie, and is absent from HTTP request URLs and served HTML.
The service enforces exact Origin, subprotocol, endpoint, actor and capability
registration. ICE server configuration reaches both WebRTC peers.

The browser entrypoint creates a `<video>` viewport, status overlay, normalized
input surface and the shared `GroupPanel` workbench without creating a
`MolSysViewerController`, `PluginContext`, local canvas or WebGL context. It
requests Python's canonical `panel` snapshot after registration, consumes later
`op` projections through the same UI-only adapter, and emits semantic workbench
actions as human-attributed runtime envelopes. Correlated transport requests
retain their envelope through `RemoteViewChannel`; ordinary commands still
arrive at `MolSysView` as accepted domain payloads. A bounded single-writer
queue preserves projection order toward the browser.

The real spika vertical E2E loads the pentalanine demo array-native into the
NVIDIA GTX 1080 worker, negotiates WebRTC with a second Chromium process,
decodes frames at exactly 1920x1080, proves zero client canvases, renders the
canonical Whole panel, executes hide-Whole UI -> Python -> worker/UI roundtrip,
changes the authoritative representation to `spacefill`, drives camera input
through the authenticated DataChannel, seeks and steps the real trajectory
through a controller-free projected scrubber, and performs a real Mol* molecular
pick whose selection is accepted by Python and reprojected to the UI-only workbench.
Selection reprojection is deliberately idempotent so the render worker,
workbench and embedded viewer converge without a second history operation.
Trajectory uses the same authority rule: the browser emits semantic intent,
Python validates and stores frame/playback state, and the worker renders the
projection while reporting playback progress. `set_trajectory_summary` is part
of the canonical panel snapshot and live projection, so a browser or future Qt
client attaches without molecular coordinates or a local Mol* controller.

The E2E also guards first-frame startup. A negotiated canvas track can be live
while still reporting zero source frames when the WebGL scene finished drawing
before the remote description existed. Initial capture requests therefore force
a fresh renderer draw after negotiation; worker-side track and outbound-RTP
diagnostics make a recurrence distinguishable from ICE, codec or decoder failure.
The shared Export panel now completes both server-rendered workflows. PNG
requests are rendered by the GPU worker and returned to Python; standalone HTML
is built directly from Python's canonical snapshot. Neither writes to a path on
the server. Both become bounded, session-ephemeral artifacts (32 MiB each, four
retained), receive unguessable URLs, and are downloadable only with the
session's `HttpOnly` cookie. The browser client validates same-origin URLs and
the E2E verifies the downloaded PNG signature and self-contained HTML document.
The browser distinguishes negotiating, ready, degraded, disconnected and
failed states. An unexpected WebSocket loss creates a fresh authenticated
attachment, requests a new canonical panel snapshot and renegotiates the
WebRTC video/input peer. A server `session-closing` signal distinguishes an
authoritative shutdown from a recoverable transport loss, so a clean shutdown
does not waste retries or emit browser connection errors. The vertical E2E
forces this reconnect between initial video verification and later semantic
workflows, then observes the clean disconnected state when authority ends.

Local molecular files cross an authenticated multipart upload endpoint rather
than being interpreted as server paths. The service streams one allowlisted
file into bounded temporary storage (64 MiB), invokes the normal authoritative
`load(..., mode="replace")` path and always removes the temporary file. The
controller-free browser picker reports parse/rejection errors and the canonical
projections replace stale trajectory and selection state. The real E2E uploads
a four-atom PDB after remote picking and verifies Python atom count, label,
frame and cleared selection.

The same `RemoteSessionService` now also accepts `render_on="client"`. In that
placement it creates no managed worker and advertises the authenticated human
endpoint's `render` and `structure-receive` capabilities. A WebSocket-backed
four-method model adapter invokes the exact AnyWidget `render()` entrypoint, so
the client receives the established full Mol*/workbench runtime rather than a
fork. Control remains enveloped and array-native headers retain their original
binary frames. The portable E2E verifies one local WebGL canvas, no video
surface, the real 62-atom pentalanine transfer and its completion acknowledgement.
Remote envelopes carry the registered browser endpoint and human actor instead
of the notebook-only `widget-host` default. Varela Round is now an embedded
WOFF2 resource with its OFL notice in the installed package: session CSP stays
closed to external style/font origins while retaining the intended welcome-card
typography reproducibly offline.

The client-rendered adapter now also retains its one local controller across a
transport interruption, creates a fresh authenticated socket with bounded
backoff, re-announces array-native readiness and consumes the new canonical
generation. It drops only lifecycle ACKs belonging to the interrupted binary
generation; semantic commands attempted without a connection still fail
visibly. The E2E forces this reconnect, proves that no second canvas appears,
then changes the authoritative Whole representation to `spacefill` through the
shared panel and confirms the mutation in Python. The same workflow creates a
real selection through the shared system panel, seeks and steps the trajectory,
and confirms both mutations in Python. Full-runtime trajectory controls expose
the same stable selectors as the projected controls and now route their local,
immediate changes through `interaction_context_action`, so Python remains the
reproducible authority and projects the accepted state back to every endpoint.

Export follows placement rather than pretending that a render worker always
exists. `Download PNG Image` uses the client Mol*/WebGL canvas and GPU directly.
Standalone HTML remains a Python-authored canonical artifact, published through
the authenticated bounded session download store. The client-rendered adapter
consumes that projection only after enforcing same-origin URLs. The E2E verifies
the PNG signature and downloaded HTML doctype, not merely that buttons were
clicked. The Mol*-free `RemoteFileControls` is now mounted by both rendering
placements with the same authenticated multipart transport. The client-rendered
E2E replaces pentalanine with a four-atom PDB and verifies the canonical scene
reset in Python (atom count, frame, selection and Whole state).

The client-rendered E2E also drives the real local canvas directly. A drag
produces a changed camera snapshot observed by Python after the normal debounce;
fractional clicks search the rendered molecule until Python observes a non-empty
active selection. Coordinates are relative to the live canvas bounds, not tied
to spika's resolution or GPU. Together with the server-rendered workflow, this
closes the RRS2 exit matrix for load, camera, molecular pick, selection,
representation, trajectory and export in both rendering placements.

- Add authenticated HTTP/WebSocket service.
- Implement signaling, VP8 video and reliable input channel.
- Extract UI-only entrypoint and interaction port.
- Implement browser upload/download and connection states.

**Exit:** browser completes load, camera, pick, selection, representation,
trajectory and export in both placements.

### RRS3 — remote Qt connector

**Initial connector implemented 2026-09-02.** The existing PySide6/WebEngine
application can now open an authenticated session URL with
`molsysviewer-qt --connect SESSION_URL`. It creates the normal native window
but loads the exact browser client page, preserving the fragment-to-HttpOnly
cookie exchange and sharing the server-rendered WebRTC/workbench/upload/export
implementation. It deliberately creates neither a local `MolSysView` nor a Qt
message bridge, so remote Qt does not become a second authority or protocol.
URL validation accepts only absolute HTTP(S) session URLs.

The remote shell now installs native File, View and Export menus. Their actions
activate stable controls in the shared authenticated page for molecular upload,
PNG and standalone HTML instead of introducing Qt-only transport messages.
Qt's `downloadRequested` flow asks for a destination with a native save dialog,
sets directory and filename explicitly, accepts the request and retains it until
completion. Focused tests cover actions, shortcuts, selectors, acceptance and
completion; the browser E2E drives those exact export selectors. A visible xcb
run on aleph remains before RRS3 is complete.

- Add Qt connect flow and remote channel.
- Reuse the remote web surface in `QWebEngineView`.
- Route native menus, upload, save/export and shortcuts through the session.
- Preserve current local standalone behavior.

**Exit:** visible xcb on aleph receives spika video and completes native
workflows without a remote desktop.

#### Current spika → ixtlilton → aleph acceptance command

The supported 1.0 service remains loopback-only. Its public
`molsysviewer-server` command is a thin foreground launcher for one session;
it does not imply a daemon, scheduler or multi-user service lifecycle. Start
one fixed-port session on spika; for the poor-GPU aleph case:

```bash
molsysviewer-server pentalanine --demo \
  --render-on server --port 8765
```

From a separate terminal on aleph, forward the same port through ixtlilton:

```bash
ssh -J USER@ixtlilton -N \
  -L 8765:127.0.0.1:8765 USER@spika
```

Then pass the exact quoted `Session URL` printed on spika to
`molsysviewer-qt --connect` on aleph. Keeping the same port preserves HTTP
Origin, CSP, cookie scope and the WebSocket URL. Change only `--render-on
client` to exercise aleph's WebGL/GPU instead.

The command wraps the programmatic `RemoteSessionService` and `MolSysView`
sequence used throughout the proof. It remains a one-session foreground
server, not a daemon or multi-session control plane.

The SSH forward carries HTTP and WebSocket traffic. Server-rendered media is a
separate WebRTC path: direct host candidates are not reachable across the
aleph → ixtlilton → spika topology, so the validated server-rendering path uses
TURN/TCP over its own SSH-forwarded port. Arbitrary deployments likewise need
an administratively supplied TURN service. A successful page/session connection
followed by failed ICE is therefore reported as a media-connectivity failure,
not worked around with desktop streaming.

### RRS4 — hardening, packaging and deployment

**Lifecycle recovery implemented 2026-09-02.** `RemoteSessionService` owns a
single worker monitor because it is the component that can coordinate process,
internal endpoint, client state and WebRTC renegotiation. An unexpected process
exit or worker-transport loss consumes the managed worker's one permitted
restart. The host detaches the stale socket, discards its outbound queue, waits
for the new authenticated `ready`, and the normal Python handshake retransmits
the canonical scene. An attached human endpoint then receives a fresh
`peer-start`. The client exposes `recovering`, `recovered` and terminal `failed`
states rather than presenting a frozen viewport.

The real spika E2E terminates Chromium after the first decoded 1080p video,
observes a different PID, a second complete array-native structure transfer and
a distinct connected WebRTC peer, then completes the existing representation,
trajectory, PNG/HTML, camera, picking and upload workflow. A deterministic guard
covers the race where Chromium and its socket have both disappeared before the
monitor wakes.

Static scenes are not classified as stalled merely because Mol* has nothing new
to draw. The worker requests one captured keepalive frame every two seconds, but
the 2026-09-04 Qt smoke showed that Chromium can still omit unchanged canvas
frames. The former client-side eight-second decoded-frame watchdog therefore
closed healthy peers repeatedly and was removed. Recovery currently follows
the WebRTC connection states. A future frozen-media detector must use RTP/media
statistics that distinguish an unchanged scene from a broken route.

**Foreground server CLI implemented 2026-09-02.** `molsysviewer-server` is a
thin public adapter over that service. It requires explicit placement, supports
fixed or dynamically assigned loopback ports, configurable Chromium/GPU policy
and ICE URIs, emits human connection guidance or a versioned JSON startup
record, distinguishes load/session/worker exit failures and installs signal
handlers before announcing readiness. A subprocess guard proves clean
`SIGTERM` shutdown without assuming a particular GPU.

**Input rate guard implemented 2026-09-02.** The render worker accepts at most
240 validated remote input events per one-second window. Normal clients already
coalesce pointer motion to animation frames; the additional worker-side bound
protects the real Mol* DOM path from a syntactically valid but abusive WebRTC
peer. Its guard uses an injected clock in tests and therefore does not encode
spika's timing, GPU or display resolution.

**Loopback session isolation implemented 2026-09-02.** Authentication cookies
carry a session-specific name because browser cookies are scoped by host and
path, not TCP port. Two foreground servers on different loopback ports can now
remain authenticated in one browser without overwriting one another. A real
two-service guard also proves distinct session identity, cross-token rejection
and that a download capability issued by one service is absent from the other.

Rejected WebSocket origins, subprotocols and malformed registrations do not
consume the single-client slot or mark the authoritative service itself as
failed. The last rejected peer error remains separately observable as
`last_client_error`; a valid authenticated client can attach afterwards.

Bearer authentication permits at most eight failed guesses in a rolling
60-second session window and responds with `429` plus `Retry-After` thereafter.
The actual constant-time-matched token remains usable and clears the failure
window, so the limiter cannot lock out a client that possesses the credential.

The authentication body is independently bounded to 4 KiB and client
WebSocket messages to 1 MiB. The application's larger 64 MiB allowance exists
only so the multipart molecular upload handler can enforce its streaming file
limit; it is not inherited accidentally by credentials or control traffic.

**First remote visual smoke completed 2026-09-04.** A browser on aleph reached
the Python authority and NVIDIA GTX 1080 render worker on spika through
ixtlilton, without a remote desktop. HTTP/WebSocket control worked immediately,
including projected trajectory controls. Direct WebRTC did not: both Chromium
peers exposed only UDP host candidates hidden behind unrelated mDNS names, so
ICE remained `new` despite a stable SDP exchange. An authenticated coturn relay
bound to spika loopback and forwarded to aleph over SSH as TURN/TCP established
the media and data-channel path. The client displayed pentalanine, accepted
camera input and advanced playback. The native Qt client then passed the same
functional smoke: rotate, scroll zoom, atom picking with residue highlight,
trajectory play and direct frame-slider navigation all worked. Qt now mirrors
the shared page connection state in its native status bar and clears it once
the remote peer is ready.

The smoke also exposed the correct failure UX and a performance follow-up. A
15-second route deadline now replaces an indefinite `Starting remote video`
state with an actionable TURN/client-rendering message. On the double-TCP path,
the initial 1920x1080 stream observed roughly 1.5 Mbit/s available outgoing
bandwidth, about 290 ms RTT and only a few encoded frames per second. An
explicit 1280x720/24 configuration looked somewhat better but was not yet fully
sharp or fluid. Treat adaptive resolution/frame-rate, degradation policy and
representative bandwidth measurements as quality work after the four-mode
functional smoke matrix; do not encode spika-specific timing or topology into
defaults.

**Four-mode visual matrix completed 2026-09-05.** With Python authoritative on
spika and the clients on aleph through the same SSH jump, both client-rendered
placements (browser and native Qt shell) displayed pentalanine sharply and
fluidly. Camera rotation, zoom, picking, trajectory playback and seeking all
worked. They also retained the full local viewer surface, including the Mol*
context menu and the Reset and Help controls. Client rendering required no
TURN media path because scene data and commands use the authenticated session
transport while Mol*/WebGL execute on aleph.

Both server-rendered placements passed the functional interaction smoke after
TURN/TCP was supplied, but they exposed an intentional implementation gap that
must not be mistaken for visual parity: their UI-only projected workbench did
not initially reproduce every control owned by the integrated viewer. The 1.0
work therefore defines and implements minimum server-rendered control parity
explicitly; it does not claim that the video client is pixel-identical to the
full standalone. Quality adaptation and complete UI parity remain separate work.

The 1.0 parity inventory is deliberately capability-based rather than
pixel-based:

| Surface | 1.0 decision | Reason |
|---|---|---|
| Reset camera | Required | Recovery from a lost viewpoint is basic viewport operation; the command already belongs to the canonical scene API. |
| Fullscreen | Required and client-local | It changes only the local browser/Qt presentation and needs no server protocol. |
| Accurate Help and `H` | Required and client-local | Remote users must be shown only controls that actually exist in that placement. |
| Open/close Studio and `N`/`W` | Required and client-local | The projected workbench is already the server-rendered editing surface. |
| Target-aware context menu | Required; implemented for the canonical remote-safe action set | Mol* picks on the worker, Python projects a sanitized correlated target only to the human endpoint, and the client renders the shared menu locally. Interactive measurement-tool startup remains a separate parity item. |
| Background, spin and swing toolbar state | Required only through the existing Studio controls for 1.0 | Duplicating toggles in the canvas toolbar without authoritative projected state would create misleading controls. |
| Popup/second window | Post-1.0 | The current service intentionally owns one human endpoint; adding a second endpoint changes lifecycle and collaboration policy. |
| Identical layout and styling | Post-1.0 | Functional parity is required; pixel identity across native, browser and video-backed surfaces is not. |
| Adaptive video quality | Post-1.0 quality work | Explicit bounded video parameters already make the placement operable without hiding network-dependent policy. |

The first parity tranche adds shared remote `Reset`, `Full`, `Help` and `Panel`
chrome. Reset remains a command through the Python authority; fullscreen, help
and panel visibility stay client-local. The video-backed surface now uses the
same compact icon-button component as the normal minimal viewport instead of a
second text-button design. Qt WebEngine explicitly enables fullscreen support,
accepts page fullscreen requests and projects them onto the native window;
focused guards cover both the browser-side control and the Qt enter/leave
bridge.

The second parity tranche adds target-aware right click without duplicating
picking. The local client sends a normalized, correlated context-menu input;
the real worker canvas and Mol* resolve the target; Python removes worker-only
coordinates and object references and projects the target only to the attached
human endpoint. The browser or Qt WebEngine then opens the shared
`ViewerContextMenu` at the original local pointer position, so its text and
controls remain sharp even when the molecular viewport is compressed video.
The menu exposes only actions that cross the existing authoritative command
gateway correctly. Distance/angle/dihedral tool startup, viewer-mode changes,
canvas hiding and a second workbench surface remain hidden until their remote
semantics are implemented; an unavailable action must not be presented as if
it worked.

Restoring MolSysMT's canonical 5000-frame pentalanine H5MSM artifact exposed a
hidden E2E dependency on its accidentally truncated 100-frame replacement: the
self-contained HTML export is 24.07 MiB and narrowly exceeded the original
24 MiB remote-artifact ceiling. The bounded ceiling is now 32 MiB (still four
ephemeral artifacts per session), which admits the official demo without
weakening the single-session retention model or teaching the test to use a
reduced trajectory.

- Declare server dependency rather than relying on a transitive package.
- Add token, origin, malformed-message, rate/size and isolation guards.
- Document LAN/VPN, reverse proxy and configurable ICE deployment.
- Synchronize the UIBCDF Qt package family.
- Add diagnostics and release-facing failures.

The loopback gateway items above are implemented and guarded, and the visible
browser/Qt matrix from aleph is complete. Final closure still requires
repetition from a clean supported installed environment; broader proxy/TURN
administration remains outside the direct single-session server boundary.

**Exit:** all four combinations pass, packaging is reproducible, and the
documented spika-to-aleph workflow repeats from a clean supported environment.

## 14. Acceptance matrix

Use real demo viewers, not mocked molecular runtimes. Cover `dialanine`,
`pentalanine`, `tctim` and `chicken_villin_HP35` where meaningful.

| Area | Required evidence |
|---|---|
| Four modes | browser/client, browser/server, Qt/client and Qt/server load |
| Authority | one command, one public mutation, at most one checkpoint |
| Interaction | camera, hover, pick, selection, context action and measurement |
| Projection | whole, regions, layers, shapes, annotations and measurements align |
| Trajectory | seek/playback remain coherent with authority |
| Native Qt | menus, upload, save/export, shortcut and clean disconnect |
| Server CLI | one foreground session; both placements; source/empty startup; machine-readable result; useful exit codes and signal cleanup |
| Lifecycle | worker restart, stale endpoint, reconnect and server termination |
| Isolation | no cross-talk between independent viewer/session identities |
| Security | invalid token/direction/input/upload rejected visibly |
| GPU | real renderer reported; silent SwiftShader rejected server-side |
| Video | VP8; explicit dimensions/fps/bitrate; stall/ICE failure observable |
| Packaging | corrected UIBCDF family and real WebEngine smoke pass |

Record representative performance rather than hide it behind one number. The
initial spika targets are usable 1080p/30 for one session, small-system startup
under ten seconds, and no unbounded RSS/queue growth. Release thresholds come
from the implemented end-to-end path, not copied from feasibility probes.

Portable GPU acceptance requires WebGL2, a non-empty renderer and rejection of
known software renderers; it never requires a particular GPU vendor or model.
An installation-specific certification job may set `MSV_EXPECTED_GPU_REGEX`
(for example to verify that a named cluster node reached its assigned GPU).
That optional assertion is a deployment profile, not a MolSysViewer product
requirement.

## 15. Explicitly post-1.0

- remote collaboration and multi-user mutation authority;
- managed TURN and arbitrary NAT/firewall reachability;
- automatic TLS certificate provisioning;
- cluster scheduler/job submission and worker migration;
- background service management, multi-session control plane and durable
  session restoration;
- institutional authentication, scoped credentials, quotas and tenant
  accounting;
- GPU-worker pools and multi-tenant accounting;
- hardware encoder selection and NVENC optimization;
- adaptive bitrate/resolution/codec and automatic rendering placement;
- synchronized viewports and collaborative cursors;
- offline continuation after authoritative server loss;
- MolSys-AI agent and chat product itself.

The deferrals retain 1.0 extension points: ICE configuration, capabilities,
explicit placement, actor provenance and cancellation identity are part of 1.0
so later work extends rather than replaces it.

## 16. Rejection criteria

The implementation is wrong if it:

- streams a remote GNOME desktop or application window as product protocol;
- creates separate browser and Qt server architectures;
- gives the worker reproducible mutation authority;
- initializes Mol*/WebGL in the server-rendered client and merely hides it;
- sends all coordinates to a poor-GPU client unnecessarily;
- uses screenshots over WebSocket as steady-state video;
- relies on Playwright or a public DevTools port in production;
- silently selects SwiftShader, placement, resolution or filesystem;
- creates a special DOM-control path for MolSys-AI;
- claims general cluster/Internet reachability without ICE/TURN and security
  evidence.

## 17. Immediate next step

RRS2 is complete. Complete RRS3 with visible xcb acceptance on aleph; do not
create a separate Qt protocol or regress local standalone behavior. Worker
restart and video-stall recovery are now implemented as portable lifecycle
logic. Continue RRS4 with connection-state projection, security/isolation, the
reproducible loopback/SSH deployment workflow and the guarded foreground
`molsysviewer-server` contract from section 9. Do not expand that command into
a service manager, and do not introduce a desktop-streaming wrapper, a hidden
Mol* runtime in the server-rendered client or a second scene authority.
