# JS/TS workflow

Use this page when you work on the TypeScript runtime.

## Source of truth

- TypeScript sources: `molsysviewer/js/src/`
- Generated artifacts:
  - `molsysviewer/viewer.js`
  - `molsysviewer/viewer.js.map`

Do not edit generated artifacts by hand.

## Install and build

```bash
cd molsysviewer/js
npm install
npm run build:runtime
```

`npm run build:runtime` is the normal development rebuild. It regenerates
`molsysviewer/viewer.js` and `molsysviewer/viewer.js.map` from TypeScript
without changing package version metadata.

Use `npm run build` only for release or packaging flows. It first runs
`sync-python-version.mjs`, which rewrites `molsysviewer/js/package.json` from
the Python `versioningit` output. In a dirty tree that can change
`pythonVersion` to a local value such as `X.Y.Z+N.gSHA.dirty`; do not commit
that churn as part of normal development.

## Test

Unit tests

```bash
cd molsysviewer/js
npm run test:js
```

E2E tests (manual, requires a browser with WebGL)

```bash
cd molsysviewer/js
npm run test:e2e
```

This runs every E2E suite against one shared Chromium process. Browser launch and WebGL2 failures
are errors by default; `E2E_ALLOW_SKIP=1` is an explicit opt-out, not the normal test mode.

On this workstation, the verified command is:

```bash
PW_CHROMIUM_BIN=/usr/bin/google-chrome npm --prefix molsysviewer/js run test:e2e
```

## Debug

- Use {doc}`debugging` for message-level debugging and popout sync issues.
- Use your browser devtools console for runtime logs.

## Awaiting a completed canvas draw

`js/src/managers/canvas-draw.ts` owns `waitForCanvasDraw(canvas, timeoutMs)`.
It subscribes to Mol*'s `didDraw`, ignores the BehaviorSubject's synchronous
replay, requests a new draw, and releases its subscription on completion or
timeout. The default deadline is 30 seconds. Exported-scene readiness and Movie
completion use this shared tool.

`PluginCommands.Camera.SetSnapshot` acknowledges a requested camera reset.
Mol* applies the reset during scene commit/draw; awaiting that command alone
does not establish a rendered final camera. Movie waits for its pending commands,
submits the last keyframe, awaits the new draw, and only then reports completion.
The playback generation check still prevents a stopped/replaced movie from
reporting completion.
