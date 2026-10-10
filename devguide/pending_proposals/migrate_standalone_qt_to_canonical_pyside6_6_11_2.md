---
summary: Migrate the optional standalone Qt host to canonical PySide6 6.11.2.
issue: uibcdf/molsysviewer#109
status: active
opened: 2026-09-27
closed:
verification: measured
area: [standalone, packaging, testing]
guard:
normative:
blocked_by: []
supersedes: []
---

# Migrate the optional standalone Qt host to canonical PySide6 6.11.2

**Reported:** 2026-09-27 during the Qt dependency simplification study.
**Status:** Active; source, tests and development/CI recipes have been updated,
and the hosted Linux Qt pipeline passed. Native Windows/macOS and visible-window
observations have not completed.
The 2026-09-28 scope decision keeps the host experimental for 1.0, so those
remaining observations are outside the core release gate.

## What

### Local probe observation — 2026-10-08

During #179 development in `molsyssuite@uibcdf_3.14`, one full Python campaign
hit eight Qt probe failures under the restricted execution sandbox. Its native
child diagnostics include `shutdown: Operation not permitted`, failed Qt
OpenGL/RHI creation and unavailable Vulkan. Rechecking outside that sandbox with
`tests/test_standalone.py::test_qt_event_transport_smoke_real_qt` still fails
before `TRANSPORT_READY:yes`: no temporary OpenGL context/RHI, no platform Vulkan,
and a D-Bus address connection error. The targeted command stopped at this first
failure; it does not constitute eight independently reproduced native failures.
No binding/environment workaround was introduced. This is a new local observation,
not a correction to the earlier exact-environment/hosted certificates or evidence
of a menu defect. Visible-window/GPU and native host qualification remain separate;
the optional Qt host is experimental.

The 2026-10-10 API follow-up full execution outside the sandbox reproduces all
eight transport/generation/HTML-probe failures in this development environment:
temporary OpenGL context/RHI creation fails, Vulkan is unavailable and the child
reports the D-Bus address connection error. The complete result is 3056 passed,
9 failed, 23 skipped; the ninth failure is a superseded Region query policy test,
corrected and checked separately. See
[the API follow-up](../public_api_followup_20261010.md) for the source receipt.
No Qt workaround, recertification or passing host claim was introduced.

The standalone Qt host should prefer official PySide6 6.11.2 and retain the
UIBCDF namespaced family as a fallback during the suite-wide observation
in `uibcdf/molsyssuite#57` is open. The platform-support contract remains in
`uibcdf/molsysviewer#97`; changing the loader does not itself certify a
platform.

## How

The loader selects `PySide6` if that namespace imports and otherwise selects
`PySide6_uibcdf`. An explicit `MOLSYSVIEWER_QT_BINDING=uibcdf` override
supports rollback even if both namespaces are installed. It imports every Qt
module from the selected family and never silently switches families when the
canonical namespace exists but its WebEngine module or native runtime fails.
The Qt CI lane and development Conda
recipe pin matching `pyside6`, `qt6-webengine` and `qt6-positioning` 6.11.2
from conda-forge. The old UIBCDF packages and repositories are not removed.

## Why

The five-package UIBCDF fork stack required costly native builds and careful
version alignment. Official 6.11.2 now provides a viable Linux route for the
public MolSysMT/MolSysViewer pair on Python 3.11–3.14. Cross-component
retirement decisions belong to the central observation issue, not this local
implementation report.

## What is measured and what is assumed

On 2026-09-27, clean Linux x86-64 Conda environments with public
`molsysmt=0.22.4`, `molsysviewer=0.23.4`, and conda-forge PySide6/Qt 6.11.2
resolved and passed real WebEngine event transport and payload-generation
probes on Python 3.11–3.14. After the source change, a fresh Python 3.14
environment at `/tmp/molsysviewer-canonical-6112-314` passed
`python -m pytest --receptor=llm -n 12 tests/test_standalone.py`: 42 passed,
2 skipped. The skips are graphical/GPU observations, not a full render pass.
Tests used the source checkout and public installed package dependencies.

One full Python-suite run in that deliberately minimal environment yielded
2,096 passed, 17 skipped and 10 failures. All ten failures were attributable
to missing test-environment packages (`jinja2`, `mdtraj`, `pyyaml`, `imageio`,
or `python-build`), not Qt; these are already declared in
`devtools/conda-envs/test_env.yaml`. After installing them, the affected
test selection passed 42/43; the sole remaining wheel-build test then passed
after installing its declared build frontend and backend. The full suite was
not rerun a second time, per repository test-run discipline. Do not describe
this as a green full-suite run.

The manually dispatched [hosted CI run
36338541516](https://github.com/uibcdf/molsysviewer/actions/runs/36338541516)
passed 7/7 jobs at exact commit
`19dadc1a0adb1ff7477fe9e7866e807b015c8f36`: six ordinary Python cells
and the Linux Xvfb/software-WebGL Qt pipeline using canonical 6.11.2. The
pipeline checks completion and payload delivery, not visible framebuffer
correctness or a native macOS/Windows Qt window.

The host's former local Python 3.14 development environment used UIBCDF Qt
6.10.1 and failed two real WebEngine subprocess tests headlessly. On
2026-09-27 the shared environment was migrated to official Qt 6.11.2, with
all five UIBCDF packages removed. The migrated environment passed 54
standalone/transport tests (two expected skips), 63 distribution/movie tests
(one expected skip), 116 MolSysMT–Viewer integration tests, an Xvfb real-window
smoke, and an Xvfb/SwiftShader full-render smoke. Its fresh sibling prefix
also passed the same targeted checks. This supersedes the old host-local
observation, but does not certify visible-window rendering or native
Windows/macOS operation. Windows and macOS ARM have solver-only Conda evidence;
macOS Intel lacks conda-forge Qt WebEngine 6.11.2 and is now outside the
supported matrix (`uibcdf/molsyssuite#59`); its PyPI wheel route is not a
pre-1.0 gate.

A full Viewer suite was run once in the fresh shared-recipe prefix before
adding `python-build` and `imageio` to that recipe and updating a test that
still expected the former `macos-latest` runner. It yielded 2,132 passed,
17 skipped, three failed. The affected test files then passed, but the full
suite was not rerun. This is not a green full-suite result.

### Interaction integration run in an older environment (2026-09-30)

The Interactions consumer check under `uibcdf/molsysviewer#114` used the existing
Python 3.13 prefix `molsyssuite@uibcdf_3.13`, not the canonical 6.11.2 recipe.
One full run, `python -m pytest --receptor=llm -n 12 tests/`, reported
2,200 passed, 18 skipped and three crashed workers. The affected nodes were
`test_qt_event_transport_smoke_real_qt`,
`test_qt_payload_refs_replace_across_two_real_generations` and
`test_qt_live_model_smoke_real_window` in `tests/test_standalone.py`.

A focused serial invocation reproduced exit 139 on the first node. The native
trace ends at `standalone_qt/utils.py:104`, importing `PySide6.QtWebEngineWidgets`,
before the transport child process runs. The installed inventory mixes
conda-forge `pyside6=6.9.3` and `qt6-main=6.9.3` with PyPI
`pyside6-addons=6.9.2`, `pyside6-essentials=6.9.2`, and UIBCDF 6.9.2
binding/WebEngine packages. This is outside the agreed canonical recipe.
The mixed inventory is a diagnostic finding, not proof of the exact native
fault mechanism. No environment or Qt source changes were made in that task.
Do not count that full run as green or as a regression of qualified 6.11.2.

## Alternatives and refuted paths

Removing the fork family now would discard rollback capacity before hosted and
platform gates. Falling back from a partially broken canonical installation
would mix or hide incompatible native libraries; only absence of the canonical
namespace or an explicit rollback selection triggers fallback. Treating a
successful solver as a platform
certificate was rejected.

## Scope and acceptance

This report owns Viewer code, tests, recipes and CI changes. It does not own
suite-wide retirement policy, platform-support wording or package deletion.
Before closure, confirm the remaining native-platform policy and tests, the
source package candidate, and the maintained installation/support matrix.
`tests/test_standalone.py` is the prospective guard;
record its final relevance and exact hosted evidence at closure.


### Follow-up during native Interactions integration (2026-09-30)

The single full-suite run `python -m pytest --receptor=llm tests/ -n 12`
reported 2,212 passed, 18 skipped and four failures. Three were the same native
Qt import worker crashes, at `standalone_qt/utils.py:104`, in
`test_qt_event_transport_smoke_real_qt`,
`test_qt_payload_refs_replace_across_two_real_generations` and
`test_qt_live_model_smoke_real_window`. The fourth was the E2E inventory's old
37-suite count; it was updated to 38 after registering the new scientific
browser suite and its targeted inventory/protocol selection passed 130 tests.
No second full-suite run or Qt environment change was made. The current Qt
qualification remains the finding recorded above, not a passing standalone gate.

### Hosted WebGL initialization observation — 2026-10-06

At Viewer commit `0f7b386a0c1ce132d93fdaaa962f96bdf8219dba`, CI run
`37438222739`, Qt job `112185249716`, completes environment provisioning
including RDKit but fails `test_qt_live_model_smoke_real_window`: the bridge
reports `Exported scene has no WebGL canvas`. Native stderr identifies
`Could not create a WebGL rendering context` and Mol* initialization failure.
The D-Bus and Vulkan messages are accompanying diagnostics, not a demonstrated
root cause. No frame was rendered and this result supplies no visual certificate.

This remains an experimental-host qualification finding under #109. It does
not establish a new core product defect or alter the accepted standalone
experimental boundary for 1.0. No Qt workaround or opt-out is introduced.

### Local support-library receiving observation — 2026-10-06

The single complete Viewer source run during public SMonitor 0.19.0 / ArgDigest
0.15.0 receiving returns **2,879 passed, 23 skipped, two failed**, exit 1, in
507.07 s. Development uses `molsyssuite@uibcdf_3.14`, Python 3.14.7, editable
SMonitor `f604b940ab281df4554869fdd24f796ea6d42c27`, ArgDigest
`5c6711ebfe23b9516ef0e8f830abee70589ec406` and MolSysMT
`ce4cfe2b817e3721ac4681be2c251ad4a13c520e`. The new application-policy guard
and the library sources are those published at Viewer `a48478fc`.

Both failures are in `tests/test_standalone.py`:
`test_qt_event_transport_smoke_real_qt` supplies no `TRANSPORT_READY:yes`, and
`test_qt_payload_refs_replace_across_two_real_generations` supplies no JSON
report. Their trivial pages do not load Mol* or request a WebGL canvas.
Nevertheless, native Qt stderr reports `QRhiGles2: Failed to create temporary
context`, `Failed to create context` and `Failed to create RHI for backend:
OpenGL`, with Vulkan/software fallback and D-Bus diagnostics. This is failure
to initialize the host process, not a demonstrated protocol or support-library
failure. The accompanying diagnostics do not identify the precise cause.

Canonical PySide6/QtCore are both 6.11.2; the shared development process has
neither `DISPLAY` nor `WAYLAND_DISPLAY`. The test fixtures already select
offscreen, so this does not demonstrate why the native context fails. The
same candidate's public CI run `37530734861`, completed Qt job
`112499151380`, separately fails `test_qt_live_model_smoke_real_window` with
`Exported scene has no WebGL canvas` and `Could not create a WebGL rendering
context`. This repeats the hosted initialization observation above, rather
than establishing a failure in SMonitor/ArgDigest receiving.

These observations extend the existing experimental-host finding; they are
not a passing full suite or standalone qualification. No graphical backend
override, environment edit, opt-out or repeat full run is made. Separately,
122 bounded tests with the exact public support archives in a fresh non-Qt
installed environment pass. The exact receipts and full-source distinction
are retained in [the receiving record](../support_library_receiving_20261006.json).

### Canonical 0.24.1 candidate observation — 2026-10-08

Manual staged CI `37760422583` at exact Viewer
`ae1fb995d6a38f2df6df206d2af26fbde1531f24`, with canonical Viewer 0.24.1
and staged MolSysMT 1.0.0, fails Qt job `113255218995` in
`test_qt_live_model_smoke_real_window`, `tests/test_standalone.py:1937`.
The bridge again reports `Exported scene has no WebGL canvas`; stderr reports
`Could not create a WebGL rendering context` and Mol* initialization failure.
D-Bus/Vulkan diagnostics and a subsequent CDN import failure are preserved,
without attributing the initial context failure to them. The downstream
structure-loading step is skipped. No frame or visual certificate is obtained.

This repeats the existing experimental-host observation. Core browser and
Windows launcher checks for the same Viewer pass in their separate scopes;
they do not close #109. The [candidate receipt](../stabilization_0241_preparation_20261008.json)
retains the exact pair and pending source/installed qualification. No Qt
workaround, opt-out or test rerun is introduced.
