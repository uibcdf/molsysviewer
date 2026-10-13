# Core qualification and experimental native Qt diagnostics

**Normative scope — 2026-10-13, uibcdf/molsysviewer#231.** Qt standalone
remains experimental for 1.0. Its actual process/window/GPU diagnostics run
independently of required core checks. Remote support remains post-1.0.

## Python selection

The registered `qt_runtime` pytest marker covers only real native Qt process,
window, GPU and associated resource probes. Pure Python bridge/transport,
serialization, CLI and ownership contracts remain in core. Playwright/Chromium
PNG export remains in core. Ordinary unfiltered pytest still runs both scopes;
no global skip, environment workaround or assertion suppression is introduced.

Core source/release validation selects the full core suite explicitly:

```bash
python -m pytest tests/ -m "not qt_runtime"
```

Native Qt diagnostics select the complementary scope:

```bash
python -m pytest tests/ -m qt_runtime
```

The latter requires its qualified binding/host and the existing display/GPU
options for those observations. A skip or launch/render failure does not qualify
Qt. Software Xvfb checks remain separate from visible native-GPU certification.
Add actual native Qt probes to this marker; never mark pure contract tests just
because their name mentions Qt. `tests/test_core_qt_gates.py` checks actual
collection, exact native cases, retained bridge/Chromium coverage and wiring.

## Hosted workflows and release checks

- `CI.yaml` requires all six Linux/macOS Python cells and JS checks. Its existing
  `PR full suite` status name is preserved for branch-rule compatibility; its
  aggregate requires the complete **core** matrix only.
- `ci-python-314-source-pair.yaml` retains exact provider/source provenance and
  all three native Python 3.14 hosts, selecting the same full core suite.
- `CI_qt_experimental.yaml` owns the native Qt diagnostics and their official
  failure conclusions. Window, software-WebGL and offscreen/resource steps all
  remain executable; after successful setup, later diagnostics still run after
  an earlier diagnostic fails. Their JUnit is retained for 14 days. There is no
  `continue-on-error`, ignored exit code or passing certification claim.
- The local `release_gate.py` Python step selects full core. Exact candidate,
  staging/public artifacts, citation/version and hosted core checks remain
  mandatory; this classification does not waive those gates or authorize release.

## Independent recovery

`ci_backlog.py` uses independent `ci`, `e2e` and `qt` watermarks. A historical
CI run officially failed solely on its former Qt job can prove that its six
core cells/JS completed; its original failed conclusion stays unchanged.
Failed, missing or skipped required core steps and unknown nonpassing jobs
cannot clear core debt. Failed or incomplete Qt diagnostics cannot clear Qt
attempts, and successful core does not qualify Qt. Network/API uncertainty
still requests a full run of the affected lane.

## Evidence ownership

Current source outcomes and later installed candidate qualification are distinct.
Keep dated logs, exact run/job identities and native diagnoses in the owning
receipt. Update current handoff state after terminal CI inspection; preserve
historical failures. Qt repairs and certification stay under #35/#109/#113;
this contract owns validation scope only. Broad docs precede the eventual
0.25.0 producer freeze. Build/qualify its exact
files before the final installed first-contact review; both 1.0 publications
remain paused.

## Receiving checkpoint — 2026-10-13

#231 is integrated in source `46527392`. Local full core passes 3,095 with
21 skips, zero errors/failures; final devguide guards pass 242/242. A two-blank-
line formatting correction keeps the test AST equal; exact policy 38371766429
passes on `61c24e53`. Independent Qt 38370976385 preserves window/render
failures, while offscreen/resource probes and JUnit preservation pass. New
scientific/source-pair/core runs remain in progress in
[the receipt](core_qt_qualification_20261013.json); prior f272e384 success is not
transferred to their code or to future package bytes.
