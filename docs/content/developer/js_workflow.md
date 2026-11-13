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
npm ci
npm run build:runtime
```

The qualified build routes use Node 22; Mol* 5.13.1 requires Node >=22.
`npm ci` receives the locked dependency closure. Change the manifest/lock
deliberately when updating a dependency. Python users receive the prebuilt
runtime and do not need Node merely to display a View.

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

Core browser tests (requires a browser with WebGL2)

```bash
cd molsysviewer/js
npm run test:e2e:core
```

This runs the mandatory core suites against one shared Chromium process.
Remote preview diagnostics retain the separate `test:e2e:remote-portable` and
qualified-host `test:e2e:server-gpu` routes. `test:e2e:all` includes those previews;
their exclusion from core is not remote certification. Browser launch and WebGL2 failures
are errors by default; `E2E_ALLOW_SKIP=1` is an explicit opt-out, not the normal test mode.

On this workstation, the verified command is:

```bash
PW_CHROMIUM_BIN=/usr/bin/google-chrome npm --prefix molsysviewer/js run test:e2e:core
```

## Debug

- Use {doc}`debugging` for message-level debugging and popout sync issues.
- Use your browser devtools console for runtime logs.

## Native dependency comparison probes

Auxiliary entries outside the JS package can resolve an ancestor's Mol*
installation. Setting a working directory alone does not select a provider.
Use the qualification builder with an explicit package directory and version:

```bash
node scripts/build-molstar-probe.mjs /absolute/probe.ts \
  /absolute/node_modules/molstar /new/output/probe.cjs 5.13.1 cjs
```

For a browser probe, use `iife` and a final global name. The builder checks the
package identity, aliases native imports, rejects a foreign native origin and
records the original bytes supplied to esbuild in `probe.cjs.inputs.json`.
It rechecks those files before emitting and refuses existing output files.
Compare that manifest with the selected public artifact when making a
published-version claim. Probe assertions define behavior; an origin manifest
alone does not qualify rendering, memory or compatibility.

This diagnostic route consumes unmodified native code. It does not replace
the ordinary runtime/unit/harness builders or their reviewed compatibility
adapters. Keep original failures, input manifests and corrected measurements
distinct; #374 records why the earlier auxiliary attribution was withdrawn.

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
