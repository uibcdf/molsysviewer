---
summary: Panel popup bootstrap calls a private controller method and fails TypeScript validation
issue: uibcdf/molsysviewer#246
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: medium
verification: reproduced
area: [frontend, popup, typing]
guard: tests/test_panel_popup_controller_contract.py
normative:
blocked_by: []
supersedes: []
---

# Private controller access in Studio popup bootstrap

## What / How

After clean `npm ci`, `npx tsc --noEmit` fails with TS2341 at `src/index.ts:1008`:
the Studio popup bootstrap calls private `MolSysViewerController.setPanelMode`.
The call originated in 63c3d9c78 and remains in 19d92c25. Esbuild does not enforce
access modifiers, so runtime build/browser success cannot close this static gate.
The finding is independent of #242's compatible dependency changes.

## Why / resolution route

Dispatch the existing public `set_panel_mode` message after saving the host panel
state and await completion before hiding the shell/opening the popup. Keep the
method private; its state owner is the controller. Run the real TypeScript
compiler and the actual popup browser guard. No runtime popup failure is claimed
from the static diagnostic alone.

## Resolution — 2026-10-13

The popup bootstrap awaits the public handleMessage(set_panel_mode) route after
saving the original host panel state, then hides the host shell and opens the
popup. The state-changing controller method remains private.
The real compiler passes without suppressions; the guard runs TypeScript against
the actual runtime sources and fails on a returning cross-class private access.
The actual Mol*/Chromium panel-popup guard also passes Render/Clear, caller
ownership, independent endpoints and canvas Render after closing Studio popup.
This source evidence does not qualify live third-party Jupyter or package bytes.
