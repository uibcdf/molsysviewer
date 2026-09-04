(User_Remote_Sessions)=
# Remote sessions

Use a remote session when the Python process or molecular rendering should run
on a workstation, server, or cluster node while you interact from another
computer. You do not need to stream a complete remote desktop.

MolSysViewer keeps one authoritative Python session on the server and lets you
connect with either your browser or the native Qt shell.

## Choose where rendering runs

Choose the placement explicitly when you start the server:

| Option | Where Mol* and WebGL run | Use it when |
|---|---|---|
| `--render-on client` | Your browser or Qt WebEngine | Your local computer has a suitable GPU |
| `--render-on server` | A managed Chromium worker on the server | The server GPU is preferable |

There is no automatic placement. The server will not silently move rendering
between machines.

## Start one server session

On the server, start a foreground session with a bundled demo:

```bash
molsysviewer-server pentalanine --demo \
  --render-on server --port 8765
```

To render on the client instead, change only the placement:

```bash
molsysviewer-server pentalanine --demo \
  --render-on client --port 8765
```

A normal molecular-system path refers to the **server filesystem**:

```bash
molsysviewer-server /data/project/system.pdb \
  --render-on server --port 8765
```

Pass `--port 0` if you want the operating system to choose an available port.
The command prints the selected port and an authenticated session URL. Keep the
process running; pressing `Ctrl+C` closes the session and its render worker.

Server rendering requires hardware rendering by default. Use `--chromium PATH`
to select a Chromium-family executable. `--allow-software-rendering` is an
explicit diagnostic or compatibility choice, not the production default.

## Connect from a browser

Forward the printed port from your local computer when the server is reachable
through SSH:

```bash
ssh -N -L 8765:127.0.0.1:8765 USER@SERVER
```

Then open the exact `Session URL` printed by `molsysviewer-server` in your local
browser.

If access passes through a jump host, use `ProxyJump`:

```bash
ssh -J USER@JUMP_HOST -N \
  -L 8765:127.0.0.1:8765 USER@SERVER
```

Use the same local and remote port so the printed URL remains valid.

## Connect with the Qt standalone shell

After establishing the same SSH forward, run this on your local computer:

```bash
molsysviewer-qt --connect "SESSION_URL"
```

You see a local native Qt window without browser chrome. Its menus, shortcuts,
file picker, save dialogs, and window management belong to your computer. The
central MolSysViewer surface comes from the server session.

With client rendering, Mol* uses the GPU exposed by your local Qt WebEngine.
With server rendering, the molecular viewport is VP8 video produced by the
server GPU and your pointer and keyboard input travel back to the render worker.
The workbench and reproducible mutations still use the same Python authority in
both cases.

## Understand the network path

The SSH forward carries the session page, authentication, uploads, downloads,
WebSocket control, and WebRTC signaling. In server rendering, live video and
input use a WebRTC media path after signaling.

Direct LAN or VPN connectivity normally permits that media path. A successful
page connection followed by an ICE/media failure means the control tunnel
works but the client cannot reach a WebRTC candidate. MolSysViewer 1.0 does not
provide managed TURN or promise traversal through every NAT or institutional
firewall.

You can repeat `--ice-server` to supply an administratively available STUN or
TURN URI:

```bash
molsysviewer-server pentalanine --demo --render-on server \
  --ice-server stun:stun.example.org --port 8765
```

TURN servers require a username and credential. Keep the password out of the
command line by naming the environment variable that contains it:

```bash
export MOLSYSVIEWER_TURN_PASSWORD='replace-with-the-issued-secret'
molsysviewer-server pentalanine --demo --render-on server \
  --ice-server 'turn:relay.example.org:3478?transport=tcp' \
  --turn-username molsysviewer \
  --turn-credential-env MOLSYSVIEWER_TURN_PASSWORD
```

MolSysViewer passes the credential only through the authenticated session
configuration; startup output does not contain it. TURN deployment and account
issuance remain administrator responsibilities.

For a constrained link, server-rendered video can be bounded explicitly:

```bash
molsysviewer-server pentalanine --demo --render-on server \
  --video-width 1280 --video-height 720 \
  --video-fps 24 --video-max-bitrate 3000000
```

These controls do not select placement automatically. Lower dimensions often
produce a more usable interactive stream than forcing 1080p through a limited
or high-latency path.

## Open and save files safely

A source passed to `molsysviewer-server` is read on the server. A file selected
from the browser or Qt window is uploaded from the client. MolSysViewer keeps
these operations distinct so a local path is never interpreted accidentally as
a server path.

The session URL contains a temporary bearer credential. Treat the complete URL
as a password: do not paste it into shared logs, shell history, tickets, or
exported molecular state. The credential and session cease to work when the
server process ends.

## Automate startup

Use `--json` when a script or scheduler needs the connection data:

```bash
molsysviewer-server pentalanine --demo \
  --render-on client --port 0 --json
```

The command emits one versioned `session-ready` JSON record containing the
session URL, Qt argument vector, SSH-forward parameters, placement, and bounded
renderer diagnostics. This record contains the authenticated URL and must be
handled as secret output.

## Current 1.0 boundary

One invocation owns one foreground session. The command is not yet a daemon,
multi-session manager, collaboration server, cluster scheduler, certificate
manager, or institutional authentication service. It does not preserve the
session after the authoritative Python process exits.

Future managed deployments may add persistent sessions, user identity, TLS,
managed TURN, scheduler integration, GPU pools, quotas, auditing, and MolSys-AI
as an authenticated actor. Those services will build on the same session API;
they will not change the meaning of client and server rendering.

## Interpret exit status

| Status | Meaning |
|---:|---|
| `0` | Clean shutdown |
| `1` | Unexpected runtime failure |
| `2` | Invalid command-line configuration |
| `3` | Molecular-system load failure |
| `4` | Session or loopback bind failure |
| `5` | Render-worker, browser, WebGL, or GPU-policy failure |
