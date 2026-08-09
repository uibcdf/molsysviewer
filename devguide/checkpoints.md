# Development checkpoint

This is the current handoff, not a changelog. Replace its contents when the
project state changes. Detail belongs in the normative documents this points to.

## Repository state

- Branch: `main`. Phase 5 is committed as `0f907ccd`; Phase 6 is an uncommitted
  working tree based on it. Latest release checkpoint: `0.20.1`.
- Suites on the Phase 6 working tree: **1298 Python passed, 3 environmental
  skips** (`--receptor=llm -n 12`). The latest frontend validation remains the
  Phase 5 result: **271 JS**, `tsc` clean, **30/30 E2E**;
  `build:runtime` and `test:perf` passed. Phase 6 changed no TypeScript.
- `sandbox/Smoke_Test.ipynb` is developer scratch state. Never include it in a
  commit and never use it as architectural evidence.
- Generated `molsysviewer/viewer.js` is built with `npm run build:runtime`;
  never edit or inspect it as source. It now carries the version that built it.
- **Every tag publishes to npm**; conda publishes from a Release, deliberately,
  and that trigger is not to be widened without a decision.

## Where the project is

Phase 5 of
[`pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md`](pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md)
— endpoint isolation and lifecycle — is committed and awaiting independent
audit. Phase 6 — ownership audit and limited consolidation — is also
**implemented and awaiting independent audit**. Phases 0a–4b are closed; 7–10
have not started. The plan's dashboard is the authority on progress.

Phase 5 has one transfer manager and deferred queue per destination. Inactive
popup managers persist until endpoint close so generation identity remains
monotonic across live molecular reloads; completion and fallback release the
payload but do not reset that identity. The endpoint matrix and mutation ledger
are recorded in the master plan.

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
- **[molstar/molstar#1903](https://github.com/molstar/molstar/issues/1903) was
  accepted** (2026-08-07): the camera bound derived from a momentarily empty
  scene. Both changes landed verbatim in `4807179`, **unreleased** — changelog
  entry sits above `v5.11.0`, and we are pinned at `^5.4.1`. Contract S9 and
  `camera_stranded_inside_scene` stay: retiring them needs a release, a raised
  version floor, and a behaviour decision, in that order
  (`pending_proposals/report_molstar_empty_scene_camera_bounds.md`).

## Open work

**The next independent review is Phases 5 and 6 plus the automated evidence of
Phase 7.** Phases 5 and 6 are committed. Phase 7's automated seams are in the
working tree; its Qt real-window/GPU observation and human reload smoke remain
explicitly blocked on a person with the required environment.

Two measurements landed with a trigger attached rather than a change, in
[`performance/qt_payload_copies_and_endpoint_isolation_2026_08.md`](performance/qt_payload_copies_and_endpoint_isolation_2026_08.md):
host projection latency revalidated at 0.0111 ms behind an in-flight popup
stream, and Qt's
payload join peaks at **2× the payload** — irrelevant at the sizes we ship,
worth 512 MB at the 256 MB scale-budget warning. If Qt is ever expected to carry
loads near that budget, switch to the preallocated `bytearray` measured there.

### Waiting on someone who is not the next session

All of it is collected, with what each one needs and what it unblocks, in
[`pending_proposals/what_needs_a_human_2026_08.md`](pending_proposals/what_needs_a_human_2026_08.md):
the Qt validation that needs a real screen, the unreviewed `34755fb9`, the hover
telemetry question, the README's positioning, the four files waiting in
MolSysMT's tree, and the Mol\* answer. Do not re-derive that list from here.

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
