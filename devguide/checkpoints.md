# Development checkpoint

This is the current handoff, not a changelog. Replace its contents when the
project state changes. Detail belongs in the normative documents this points to.

## Repository state

- Branch: `main`. Base commit: `9074c76f`. Latest release checkpoint: `0.20.0`.
- Suites at that commit: **1293 Python passed, 3 environmental skips**
  (`--receptor=llm -n 12`), **270 JS**, `tsc` clean, **30/30 E2E**.
- `sandbox/Smoke_Test.ipynb` is developer scratch state. Never include it in a
  commit and never use it as architectural evidence.
- Generated `molsysviewer/viewer.js` is built with `npm run build:runtime`;
  never edit or inspect it as source. It now carries the version that built it.
- **Every tag publishes to npm**; conda publishes from a Release, deliberately,
  and that trigger is not to be widened without a decision.

## Where the project is

Phase 5 of
[`pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md`](pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md)
— endpoint isolation and lifecycle — is **parked at 60%**. Phases 0a–4b are
closed; 6–10 have not started. The plan's dashboard is the authority on
progress; open a slice by moving its row to `◐` before working on it.

Phase 5's remainder: the endpoint evidence matrix, real-browser
relay/reconstruction checks, full suites and a runtime rebuild.

The architecture behind all of it is normative elsewhere and does not belong
here: [`data_plane_architecture.md`](data_plane_architecture.md) for the
array-native transport, [`runtime_message_router.md`](runtime_message_router.md)
for envelopes, identity and authority, [`scene_contracts.md`](scene_contracts.md)
for scene behaviour.

## What closed in the 2026-08-03 → 06 round

Export, embedding and first contact, mostly. In order of consequence:

- **Exported pages work offline and open from disk.** One template builds both
  shapes; `runtime_source` embeds the runtime, `runtime_urls` addresses it. The
  three CDN dependencies are gone. A `file://` page cannot `import()` a sibling
  module, so a self-contained export builds its own blob URL;
  `python -m molsysviewer.preview` serves the addressed shape.
- **`export.html(background=…)`** — `auto` copies the host container's colour
  and follows its theme switch on a timer, `transparent` clears with alpha,
  `white`/`dark` are fixed. The frame's *container* is what sits behind an
  embedded view, not the page body.
- **An exported page declares what it is.** It reports a scene built by a
  different MolSysViewer version, and the Studio states, once and up front, that
  no session is behind it (`hasAuthority: false`, declared by `bootDocsView`).
- **Contract S10** — the whole's representation succeeds and never accumulates.
- **`docs/execute_notebooks.py`** gained a content-hash run mark, error
  excerpts, a non-zero exit and talking excepts; `.github/workflows/docs-notebooks.yaml`
  gates the documented notebooks with `--force`, ignoring the mark on purpose.
- **The README had never been executed.** Three of five quick-start snippets
  could not run. `tests/test_readme_quickstart_runs.py` now runs them all.
- **An exported page frames its own scene, and now a suite says so.** Measured on
  a real exported file: `radiusMax` 6.22 against a scene radius of 6.22
  (`exported-page-framing.e2e.ts`, the 30th suite). Nothing had ever opened one
  and looked at its camera.
- **Qt satisfies S8 through `QtMessageBridge`, not through the Python
  deferral** — one message in flight, released only by a *handled*
  acknowledgement. It was load-bearing and untested; pinned now, and recorded in
  Contract S8.
- **The message path was re-measured** after the render-path round: nothing
  moved (`performance/message_path_regression_check_2026_07.md`).
- **[molstar/molstar#1903](https://github.com/molstar/molstar/issues/1903)** was
  filed: the camera bound derived from a momentarily empty scene. Awaiting a
  maintainer. Contract S9 and `camera_stranded_inside_scene` stay until it lands.

## Open work, in the order to take it

Nothing below depends on Phase 5, and none of it is a feature.

1. **Transport audit items 5, 7 and 8** in
   [`pending_proposals/transport_popup_audit_followups_2026_08.md`](pending_proposals/transport_popup_audit_followups_2026_08.md):
   reconcile the retained R2/D3/D4 design records with what shipped, and two
   measurements (scene deferral during popup bootstrap; copies and peak memory
   in the Qt binary scheme).

### Waiting on someone who is not the next session

- **A3 and `pending_bugs/standalone_qt_live_demo_reload.md`** need a visible
  window and a real GPU.
- **A5** — `34755fb9` touched the load path and landed after Diego's review of
  that round; no human has seen it.
- **D1 `lazy_json_fallback_payload`, D2 hover telemetry, and the README's
  positioning** (whether sixty feature bullets stay above the quick start) are
  Diego's decisions, not work items.
- **MolSysMT** holds four uncommitted files from us: the patched
  `docs/execute_notebooks.py`, a selection-syntax proposal, a form-conversion bug
  report, and two index lines.

## Resume cautions

- Read [`runtime_message_router.md`](runtime_message_router.md) and
  [`data_plane_architecture.md`](data_plane_architecture.md) first.
- Python remains the only authority for reproducible scene state. Do not
  reintroduce `{type, data, from}` routing at any seam.
- Never let an existing popup adopt a changed `session_id`. Continuity across a
  kernel restart requires a fresh authenticated attachment and a new projection.
- Binary buffers are runtime data, never scene history. A compact replay journal
  is not a canonical state snapshot.
- Do not run E2E with `E2E_ALLOW_SKIP=1` when validating popup or rendering
  behaviour.
- Verify a document's claims against the code before acting on them. This round
  found five documents asserting states the code contradicted — including one
  that criticised exactly that failure while committing it.
