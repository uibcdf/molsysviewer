# What needs a human

**Written 2026-08-06, at the point where everything outside Phase 5 that an
assistant could finish was finished.** Seven items remain, and none of them is
blocked on effort: they need a screen, a judgement, or a hand on another
repository. They are collected here because they were scattered across four
documents and each one, read alone, looked like ordinary pending work.

Each entry says what is needed, from whom, and what it unblocks. When one is
done, close it **in its home document** — the entries below point there — and
strike it here.

---

## 1. Validate the Qt host on a real screen — *needs a GPU and a visible window*

Two things wait on the same session at a machine with a display (aleph).

**A3 — the camera change was never validated on Qt.** `takeCameraAuthority` runs
in `MolSysViewerController.create`, so **every endpoint sharing `viewer.js`
inherits it**, Qt included, and its framing now depends on `frameLoadedStructure`
rather than on Mol\*'s own reset. The exported page was verified this way on
2026-08-06 and turned out correct; Qt has no equivalent check because the two
tests that would give it skip themselves without a display:

```bash
# needs $DISPLAY — the real-window smoke
pytest -k qt_live_model_smoke_real_window

# needs a WebGL-capable environment — asserts the structure actually renders
QTWEBENGINE_CHROMIUM_FLAGS="--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader" \
MOLSYSVIEWER_QT_GPU_TEST=1 xvfb-run -a pytest -k full_render_gpu
```

Two of the suite's three permanent skips are exactly these. They are not
failures, but they mean the Qt render path is asserted by nobody on this machine.

**`pending_bugs/standalone_qt_live_demo_reload.md` — the fix is in, the
confirmation is not.** Its closure criteria are explicitly manual: alternate two
visually distinguishable demos at least ten times, confirm each replacement shows
only the requested system, confirm the status reaches `Ready.` with no failed
deliveries, and record the environment in that file.

*Unblocks:* the last unverified surface of the standalone host before 1.0.

## 2. Look at `34755fb9` — *needs a person, not a test*

A5. The `clearGlobalRepresentations` no-op landed **after** the review that
closed that round, and it touches the load path, which is the most central path
there is. Nothing is known to be wrong with it; the point is that the round
produced two cases where a fix arrived after the report it answered, and this one
was never seen.

*Home:* `open_items_after_the_2026_08_smoke_round.md`, item A5.

## 3. Answer one question about hover — *a product decision*

D2, `opt_in_hover_telemetry.md`, is blocked on a single answer: **what should
`view.hover_target` mean when telemetry is off?** Every branch of the design
follows from it. The proposal cannot proceed and should not be guessed at.

## 4. Decide what the README leads with — *positioning, not work*

`first_read_comprehension_gaps_2026_08.md` closed five of its six findings; the
sixth is a recommendation it explicitly refused to own: whether the sixty-bullet
feature inventory should stay **above** the quick start or move below it. The
quick start now runs end to end and closes with the reproducibility loop, so the
question is only what a newcomer meets first.

Deciding it archives that document.

## 5. Hand MolSysMT what is waiting in their tree — *another repository*

Four files sit **uncommitted** in `../molsysmt`, all of them ours:

| File | What it is |
| --- | --- |
| `docs/execute_notebooks.py` | patched with the content-hash run mark, error excerpts, a non-zero exit and talking excepts |
| `devguide/pending_proposals/declared_selection_syntaxes_without_implementation.md` | seven declared syntaxes, four of fourteen `(syntax, direction)` cells work |
| `devguide/pending_bugs/form_conversions_importing_nonexistent_modules.md` | three advertised conversions raise `ModuleNotFoundError`; one is a dead import |
| two index lines | in their `pending_bugs/README.md` and `pending_proposals/README.md` |

There is also a prepared explanation for their team, including the point that
running the script with `-q` avoids emitting output nobody needs to read.

*Home:* `open_items_after_the_2026_08_smoke_round.md`, item E1.

## 6. Wait for Mol\* — *upstream, not us*

[molstar/molstar#1903](https://github.com/molstar/molstar/issues/1903) reports
the camera bound derived from a momentarily empty scene, with a two-line patch
ready to offer if the direction is accepted.

Both outcomes need a decision here, and they are opposite:

- **Accepted** — `takeCameraAuthority` and the `camera_stranded_inside_scene`
  detector can both go, but only once the minimum supported Mol\* version
  includes the fix. That floor is a deliberate choice, not something to inherit.
- **Declined** — the detector becomes permanent and should be documented as
  such, rather than left looking temporary in Contract S9.

## 7. Open Phase 5, or decide not to — *the only remaining work item*

Phase 5 of the master plan is parked at 60 %, and its dashboard row must be moved
to `◐` deliberately before anyone works on it. Its remainder is the endpoint
evidence matrix, real-browser relay and reconstruction checks, full suites and a
runtime rebuild. Phases 6–10 have not started.

This is the one entry that is ordinary work rather than a human prerequisite —
it is here so the list reads as complete.

---

## Two findings parked on purpose, in case they look like oversights

Neither needs a decision now; both are recorded so nobody rediscovers them as
bugs.

- **`order_high_water_mark` grows by 4 on every state round trip.** The scene
  comes back identical, but `restored.export_state() == state` is never true —
  which is the first check a user writes to convince themselves the round trip
  worked. Cosmetic, but the fix touches ordering semantics.
- **259 python blocks in 63 `.md` files under `docs/content/` are executed by
  nothing.** The notebooks are executed by `docs/execute_notebooks.py`; the
  markdown is not. One of those blocks was broken for as long as units have been
  enforced, and was found by hand. The other 62 files are unverified.
