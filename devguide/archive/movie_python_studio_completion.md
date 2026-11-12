---
summary: Python and Studio cannot share Movie completion across event loops.
issue: uibcdf/molsysviewer#366
status: resolved
opened: 2026-11-12
closed: 2026-11-12
severity: high
verification: reproduced
area: [movie, jupyter, concurrency, studio]
guard: tests/test_movie_async_ownership.py
normative:
blocked_by: []
supersedes: []
---

# Movie Python/Studio completion

**Resolved in source — 2026-11-12.** Actual-Jupyter `614` receives both pause
directions and the full flow; `613`/`615` receive the broader Python/native
regressions. Public signatures remain unchanged. Other acceptance is separate.

Run `610` retains 17 passing ownership controls and the independent failure
`Future attached to a different loop` when the public pause method awaits a
preview owned by another running loop. The source uses a loop-bound completion
Future. Studio also reports only its own job rather than existing Python-owned
runtime activity. These are distinct from #365's scene-entry/admission race.

Keep the single existing Movie owner, use thread-safe completion adapted to
the consumer loop with cancellation shielding, and project actual runtime
activity without creating a second playback engine. A Python-owned operation
has no Studio cancellation job; Pause can still control its preview.

Acceptance requires the deterministic cross-loop and activity controls plus
both Python pause of GUI playback and GUI pause of Python playback in the
actual notebook/popup flow. Keep original deadlines, scientific coordinates,
session recovery, media output and close/late-reply assertions. #320 remains
the broader Movie requirement; installed, native Qt, hosted and human receiving
are separate.

The producer now owns a thread-safe completion adapted to each consumer loop;
shielding retains the original cancellation semantics. The private Studio
projection follows actual Python preview/capture/export activity. Runtime
publishing remains optional and does not add a renderer, worker or event loop
to headless Python construction. A Python-started job has no Studio cancel ID.

`611` passes 22 ownership/loop/activity controls; the final broader run `613`
passes 549 with nine explicit unselected/optional branches. Actual notebook
`614` receives both pause directions, GUI preview/pause, native popup camera,
PNG ZIP, independent session recovery and close/late-reply preservation. The
final [source receipt](../movie_jupyter_receiving_20261112.json) retains exact
inputs, original failures and the separate native media receiving.
