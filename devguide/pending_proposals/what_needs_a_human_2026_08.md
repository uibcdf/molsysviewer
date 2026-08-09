# What needs a human

**Written 2026-08-06 and reconciled on 2026-08-09.** Five items remain, and none
of them is blocked on implementation effort in this repository: they need a
screen, a judgement, or a hand on another repository. The former seventh item,
opening Phase 5, is complete.

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
[`../archive/opt_in_hover_telemetry.md`](../archive/opt_in_hover_telemetry.md).

## 4. Decide what the README leads with — *positioning, not work*

`first_read_comprehension_gaps_2026_08.md` closed five of its six findings; the
sixth is a recommendation it explicitly refused to own: whether the sixty-bullet
feature inventory should stay **above** the quick start or move below it. The
quick start now runs end to end and closes with the reproducibility loop, so the
question is only what a newcomer meets first.

Deciding it archives that document.

## 5. Hand MolSysMT what is waiting in their tree — *another repository*

The earlier four-file handover was resolved. Two current changes now sit
uncommitted in `../molsysmt` and need its maintainer's review:

| File | What it is |
| --- | --- |
| `devguide/pending_proposals/known_source_form_and_large_string_detection.md` | bounded source-form detection plus an explicit source-form hint, motivated by a 95k-atom PDB string |
| one index line | the corresponding entry in `devguide/pending_proposals/README.md` |

*Home:* the matching proposal in this repository and the two-file MolSysMT
working tree.

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
[`../archive/report_molstar_empty_scene_camera_bounds.md`](../archive/report_molstar_empty_scene_camera_bounds.md).

## 7. ~~Open Phase 5, or decide not to~~ — **closed**

Phases 5, 6, 8 and 9 are independently audited and closed. Phase 7 still awaits
the visible Qt observations above; Phase 10 owns the remaining release gates.

---

## One finding parked on purpose, in case it looks like an oversight

It needs no decision now; it is recorded so nobody rediscovers it as a bug.

- **259 python blocks in 63 `.md` files under `docs/content/` are executed by
  nothing.** The notebooks are executed by `docs/execute_notebooks.py`; the
  markdown is not. One of those blocks was broken for as long as units have been
  enforced, and was found by hand. The other 62 files are unverified.
