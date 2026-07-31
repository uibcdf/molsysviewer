# Popout parity in the Qt standalone host

**Status:** post-1.0, and deliberately staged rather than missing.

**Found:** 2026-07-31, while checking the July popup round against every host.

## What is true today

The Qt shell is built with `include_popout=False`
(`standalone_qt/utils.py:_rebuild_qt_html`), so **no popup window can be opened
in the standalone host at all**. `QtViewChannel.enable_popout` is `False` as
well, though that attribute is inert — Qt bakes its configuration into the shell
HTML at build time.

The consequence is not a broken feature; it is an **untested path**. The whole
popup control plane exists and is exercised only on AnyWidget:

- the `popup_actions` group of `runtime_actions.json` — eleven host/popup actions
  with the directions each may carry, validated on both ends;
- `MolSysView.build_popup_scene_snapshot(mode, endpoint)` and the canonical
  bootstrap that replaced the replay journal;
- the endpoint identity, token authentication and revocation on close/reopen.

None of it runs in Qt, so none of it is protected there by anything.

## Why this is not a 1.0 gate

`standalone_host_plan.md` §Proposed Execution Stages puts the auxiliary
panel/workbench window at **Stage 4**, explicitly "only after the single-window
host feels solid", and `standalone_direction.md` records the two-screen layout as
"not a near-term implementation target". Roadmap gate 4 asks for real-window
Qt/WebGL validation of load, interaction, context menu and the live-replacement
regression — it does not ask for popout.

`standalone_v2_evolution_plan.md` Phase 1 already lists implementing the
`createWindow` handler as an action item. This document exists so the *current*
asymmetry is recorded where the popup work can find it, not to reopen the
staging decision.

## The asymmetry worth naming

`standalone_host_plan.md` §Non-Negotiable Invariants warns about features that
work **only in standalone** because the host invented viewer logic. It says
nothing about the mirror case: a feature that works in the notebook and not in
standalone. That mirror is exactly what R3 was about — an unknown action was
rejected observably on AnyWidget and accepted in silence on Qt — and popout is
the same shape at the level of windows rather than actions.

The invariant list should be read as symmetric: **one workbench model, multiple
hosts** is violated in both directions.

## What it needs

1. A `createWindow` handler on the Qt page, mapping the request to a real
   `QWebEngineView` in its own window.
2. Building the shell with `include_popout=True` for the host that has such a
   handler, and keeping it `False` where there is nowhere for a window to go.
3. The popup channel's identity handshake over the Qt transport — the token and
   endpoint model is transport-agnostic by construction, but that is an
   assertion until something runs it.

## Acceptance

- A canvas popout opens from the Qt standalone and receives the canonical
  snapshot, with the same scene the host canvas shows.
- A panel popout opens and every Studio subpanel is populated — the Contract S1
  failure (a blank section, because a runtime-only summary was not projected) is
  host-independent and must be checked here too.
- The popup-channel E2E, or its Qt equivalent, runs against the real host rather
  than only against Chromium.
