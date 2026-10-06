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
