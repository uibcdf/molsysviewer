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
npm run build
```

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

On this workstation, the verified command is:

```bash
PW_CHROMIUM_BIN=/usr/bin/google-chrome npm --prefix molsysviewer/js run test:e2e
```

## Debug

- Use {doc}`debugging` for message-level debugging and popout sync issues.
- Use your browser devtools console for runtime logs.
