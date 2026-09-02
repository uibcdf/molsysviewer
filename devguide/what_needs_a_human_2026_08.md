# What needs a human

**Written 2026-08-06, reconciled 2026-08-13.** **Three items remain**, and none is
blocked on implementation effort in this repository: they need a screen or a judgement.
Items 3, 5 and 7 are closed and struck below rather than deleted, so a reader can tell
"done" from "never existed".

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

The check was retried on 2026-08-09. This executor had only an SSH session;
`DISPLAY=:0 glxinfo -B` was rejected by X authorization and there was no
user-owned desktop process to attach to. The item remains open rather than
substituting an offscreen or virtual-display result.

**Correction, 2026-09-02: both tests do run here, and pass.** The sentence above records a
decision not to substitute a virtual display; it was read afterwards as a finding that one
could not be used, which is not the same thing and was never measured. Under `xvfb-run`
with software WebGL, `qt_live_model_smoke_real_window` runs (it skips only on an empty
`DISPLAY`) and `full_render_gpu` runs and reaches its `assert success` — the structure
finishes loading through a real WebGL context.

They are now a CI job, `qt-pipeline` in `CI.yaml`, because catching a Qt host that is
broken outright is worth having and nothing was doing it.

**This does not close the item, and the job says so in its own comment.** Those tests
assert that the pipeline *completes*: the bridge becomes ready, the payload is served, the
load finishes. Nothing reads the framebuffer. `uibcdf/molsysviewer#64` is the standing
proof that this is a different question from correctness — every atom arrived, the load
completed, and fifty-nine of sixty protein copies were absent from the picture. A software
render that finishes would have reported that scene as fine.

So what still needs a human at a screen is unchanged and is narrower than "validate Qt": it
is **A3**, whether `takeCameraAuthority` frames the structure correctly on Qt, which is a
question about what the image shows and not about whether the load returned.

### Maintainer exemption for the 0.21.0 conda release — 2026-09-02

Granted by the maintainer, scoped deliberately narrowly, and recorded here rather than
agreed in conversation so that its limits outlive the discussion.

**What it covers.** Publishing the `noarch` conda artefact of 0.21.0 while A3 is
unobserved. That artefact does not install Qt: `pyside6-addons-uibcdf` and the four
packages beneath it are a separate manual install, the `standalone` extra in
`pyproject.toml` is deliberately empty, and the Qt stack is `linux-64` only. A user
installing MolSysViewer from conda receives the Jupyter widget, whose render path *is*
observed — 31 E2E suites in a real browser.

**What it does not cover.** Any claim that the Qt host is validated. It stays
`experimental` in `capability_audit.md`, and A3 stays open in this document. The exemption
is for one release of a package that does not ship the thing in question; it is not a
judgement that the question stopped mattering.

**Why it is defensible.** The gate exists to stop an unobserved render path being
presented as working. Here it was blocking a package that contains no Qt dependency, on
behalf of an `experimental` capability, while the release itself is what unblocks another
project's supported Python 3.13 installation path (`uibcdf/molsysmt#195`). The proportion
was wrong, not the principle.

**What lifts it.** A session at a machine with a display running the two commands above
against 0.21.0 or later, and confirming that Qt frames a loaded structure the way the
exported page was confirmed to on 2026-08-06.

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

## 3. ~~Answer one question about hover~~ — **closed**

The explicit-state option was selected and implemented. Hover transport is off
by default; `hover_target.info()` reports `telemetry_disabled` rather than a
plausible empty target, and callback registration activates transport without a
reload. The completed design record is
[`../archive/opt_in_hover_telemetry.md`](archive/opt_in_hover_telemetry.md).

## 4. Decide what the README leads with — *positioning, not work*

`first_read_comprehension_gaps_2026_08.md` closed five of its six findings; the
sixth is a recommendation it explicitly refused to own: whether the sixty-bullet
feature inventory should stay **above** the quick start or move below it. The
quick start now runs end to end and closes with the reproducibility loop, so the
question is only what a newcomer meets first.

Deciding it archives that document.

## 5. ~~Hand MolSysMT what is waiting in their tree~~ — **closed**

Both handovers were received. The source-form proposal was accepted into
`molsysmt/devguide/pending_proposals/` and the declared-selection-syntax report answered,
in their `d5b066a35`. Nothing of ours sits uncommitted in their tree.

## 6. Mol\* accepted the fix — *the decision is now ours*

[molstar/molstar#1903](https://github.com/molstar/molstar/issues/1903) was
**accepted on 2026-08-07**: both changes landed verbatim in
[`4807179`](https://github.com/molstar/molstar/commit/4807179589f43c20f38d689e4acbc3fc8590df14),
unreleased, changelog-listed above `v5.11.0`. Closed 2026-08-09. No longer a wait
on upstream — the only external event left is the release itself.

What needs a person is the **minimum supported Mol\* version**. We are pinned at
`^5.4.1`; depending on the fix means raising that floor deliberately, because a
user on 5.4.1 would lose the protection the moment `takeCameraAuthority` goes.
Only after that release exists, and only after re-verifying against it, is
retiring `takeCameraAuthority` and `camera_stranded_inside_scene` on the table —
and that is a *behaviour* decision, since it returns Mol\*'s opportunistic
re-framing. The four steps are in
[`../archive/report_molstar_empty_scene_camera_bounds.md`](archive/report_molstar_empty_scene_camera_bounds.md).

## 7. ~~Open Phase 5, or decide not to~~ — **closed**

Phases 5, 6, 8 and 9 are independently audited and closed. Phase 7 still awaits
the visible Qt observations above; Phase 10 owns the remaining release gates.

---

## One finding parked on purpose, in case it looks like an oversight

It needs no decision now; it is recorded so nobody rediscovers it as a bug.

- **The python blocks in the documentation markdown are executed by almost nothing.**
  `docs/execute_notebooks.py` runs the notebooks; the markdown is not run.
  `tests/test_documentation_pages_run.py` now executes three pages, listed in its
  `EXECUTABLE_PAGES`, and adding a page to that list is how this finding gets retired one
  page at a time.

  It is no longer hypothetical. A rename to `import molsysviewer as msv` was applied to
  import lines and not to bodies in four pages, leaving a `NameError` in each
  (`0c8fd0f2`), and the three pages written on 2026-08-13 contained three defects of their
  own that the new test caught before anyone read them.
