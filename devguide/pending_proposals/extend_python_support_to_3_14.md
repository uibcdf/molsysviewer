---
summary: Extend MolSysViewer Python support to 3.14 alongside MolSysMT.
issue: uibcdf/molsysviewer#93
status: active
opened: 2026-09-22
closed:
verification: measured
area: [packaging, ci, deps]
guard:
normative:
blocked_by: []
supersedes: []
---

# Extend MolSysViewer Python support to 3.14 alongside MolSysMT

**Reported:** 2026-09-22 during the MolSysSuite Python 3.14 transition
(`uibcdf/molsyssuite#29`). This is paired with `uibcdf/molsysmt#237`.
**Status:** Active feasibility work; no public Python 3.14 support is claimed.

The source-pair workflow includes a Windows/Python 3.14 job and pins exact
MolSysMT source commits. The first three-platform run (`35968412395`) passed
Linux; Windows stopped during test collection on a POSIX-only benchmark
import, and macOS had one WebSocket connection-loss failure. The benchmark
import now uses platform-specific memory measurement. Later runs passed
macOS, and the exact corrected pair in run `35975122014` passed the native
MolSysMT path guard and the full Viewer Python suite on Linux, macOS, and
Windows. This is a source-compatibility result, not evidence of staged
Conda installation or optional Qt-host availability on Windows.

## What

Extend the tested Python interval to 3.11–3.14 for the core MolSysViewer
package and its noarch Conda artifact, coordinated with MolSysMT's extension
and hard dependency. Preserve the existing 0.22.0 MolSysMT / 0.23.1
MolSysViewer staging campaign for 3.11–3.13 under
`uibcdf/molsysmt#195` and `uibcdf/molsysviewer#82`.

## How

1. Build and test the two source distributions in one isolated Python 3.14
   environment without treating bypassed current package metadata as a support
   claim. Check the viewer's bundled runtime resources and its real MolSysMT
   integration path.
2. Resolve code or dependency incompatibilities found by focused tests, then
   run the full Python suite. Include Linux and macOS Python 3.14 in the
   required CI matrix, retaining 3.11–3.13. Keep the recommended development
   interpreter on 3.13 unless the suite changes that policy.
3. After the pair passes, update `requires-python`, classifiers, noarch host
   and run constraints, distribution tests, and package documentation together.
   Do not edit the already-inspected staging artifact or reuse its coordinate.
4. Build a later exact staged pair and test clean installation of both packages
   across the claimed Python and platform matrix. Public release and central
   admission require independent package-channel verification.

## Why

MolSysMT requires MolSysViewer at runtime, while MolSysViewer requires
`molsysmt>=0.22.0`. Its staged 0.23.1 noarch package currently declares
`python>=3.11,<3.14`. A Conda dry run of `python=3.14
molsysviewer=0.23.1` with staging, uibcdf, and conda-forge failed on that
bound. MolSysMT's Linux Python 3.14 wheel feasibility under
`uibcdf/molsysmt#237` cannot become a supported paired installation until
MolSysViewer participates.

## What was refuted

- `noarch: python` does not itself imply support for future interpreters. One
  artifact serves the range in its metadata; its source and dependencies must
  be tested on 3.14 before widening that range.
- Changing only MolSysMT's metadata cannot solve a package pair whose viewer
  half explicitly excludes 3.14.

## Current evidence and open gates

- At the start of this work, source `pyproject.toml`, Conda recipe, and the
  Linux/macOS CI matrix stopped at Python 3.13. The candidate branch now
  widens wheel metadata and has a focused Python 3.14 source-pair CI gate,
  but the staged noarch artifact and installed-package matrix remain at
  3.11–3.13. `tests/test_distribution_artifact.py` guards metadata
  agreement. Routine development and documentation jobs use Python 3.13
  and need not move merely to add a supported minor.
- The core Python package is pure Python plus a bundled JavaScript runtime.
  The optional Qt host has a separate native dependency stack; investigate
  its Python 3.14 availability explicitly rather than silently making core
  support depend on it or claiming Qt support without evidence.
- Full source tests, installed-pair tests, cross-platform Conda resolution,
  and a new immutable release remain open. The existing 0.23.1 staging
  artifact is evidence only for its declared 3.11–3.13 interval.
- A local Linux/Python 3.14.7 pair probe built the unmodified source wheels
  from MolSysMT `fe0be24b8` and MolSysViewer `251f7759`. Both installed with
  `--no-deps --ignore-requires-python`; the installed MolSysMT Rust extension
  passed 99 exports, BCIF conversion produced 596 atoms, and a real
  `MolSysView(debug_js=True)` loaded that native system. MolSysViewer's
  MolSysMT/runtime integration selection passed 19 tests with 12 workers.
  The bypassed metadata and missing release version make this feasibility
  evidence, not a clean supported installation.
- In the isolated `python-3.14-support` worktree, candidate metadata
  `>=3.11,<3.15` built and installed without bypassing the Python bound;
  the packaged-runtime wheel test passed. `pip check` still reports that
  MolSysViewer requires `molsysmt>=0.22.0` while this MolSysMT source tree
  identifies itself as development version `0.21.0+...`. An exact later
  candidate is required before resolver-consistent pair evidence exists.
- A separate Conda dry run for `python=3.14 pyside6-addons-uibcdf=6.9.2`
  failed: its `shiboken6-uibcdf` dependency requires `python_abi=3.13`.
  This optional Qt host must not be claimed on 3.14 without a compatible
  package and its own Qt tests. The five-package UIBCDF stack is ordered
  `qt6-positioning-uibcdf` -> `qt6-webengine-uibcdf` and
  `shiboken6-uibcdf` -> `pyside6-essentials-uibcdf` ->
  `pyside6-addons-uibcdf`, with Addons also consuming both Qt runtime
  packages. Their 6.9.2 recipes all pin Python 3.13. The [upstream Qt for
  Python release notes](https://doc.qt.io/qtforpython-6/release_notes/pyside6_release_notes.html)
  describe only initial 3.14 adaptations in 6.9.2 and first declare Python
  3.14 supported in 6.10.1. A local probe did import
  the canonical 6.9.2 `PySide6.QtCore` and `QtWebEngineWidgets` ABI3 modules
  under CPython 3.14.7, but that does not validate the suffixed UIBCDF stack
  or its Conda metadata. This is a separate package-family gate; it does not
  invalidate the core notebook viewer probe above.
- The candidate branch adds a two-platform Python 3.14 source-pair workflow
  with MolSysMT pinned to exact commit
  `3485f8ddf0924f307dd8a089dea4ed8b51276600`. It exercises the full
  Viewer Python suite against locally built sources without ignoring Python
  metadata. It deliberately omits `pip check`: the source checkout's 0.21.x
  development identity is below Viewer's release floor and is not an exact
  staged pair. This workflow is a source-compatibility gate, not a release
  or package-admission gate.
- A local 12-worker full Viewer suite run on Python 3.14 collected 2,090
  tests: 2,069 passed, five failed, and 16 skipped. Four failures were
  environmental (`jinja2` and `mdtraj` omitted from the initial probe
  environment); both resolve on Linux/Python 3.14 and are now in the source
  workflow environment. The fifth was a pre-existing stale generated
  capability audit: its generator finds three first-release tags at 0.8.0
  where the checked-in document said 0.9.0. The document was regenerated.
  The three affected test files then passed 208 tests. This is not a clean
  full-suite run; the hosted two-platform workflow remains the required
  confirmation.
- GitHub cannot dispatch this new workflow while its file exists only on the
  feature branch. A draft pull request supplies the source-pair run. Its HEAD
  commit must not contain `[skip ci]`: GitHub suppresses every
  `pull_request` workflow when it does. The PR title uses that marker only
  for the repository's own older-job guards, so the focused source-pair gate
  can run without launching the existing six-cell package matrix.
- Draft PR `uibcdf/molsysviewer#94` ran the source-pair suite on Linux and
  macOS (`35825682709`). Both reached all 2,090 tests, but failed for
  incomplete probe dependencies (`Bio`), a generated audit that varied with
  a local-only unpublished `0.8.0` tag, and a Qt-shell test that used a fake
  PDB ID as real export input. macOS also exposed an assertion that treated
  `/tmp` and its resolved `/private/tmp` path as different locations. The
  dependency environment now includes Biopython, the audit generator ignores
  that unpublished tag, the Qt-shell test isolates its export-menu wiring
  while existing tests retain real HTML-generation coverage, and the path
  assertion compares resolved paths. The focused 3.14 rerun passed 237 tests
  with four optional Qt skips. Its rerun `35828199753` passed both Linux and
  macOS jobs. This validates the source-pair Python suite, not clean Conda
  installation or the optional Qt host.
- A stricter Conda solve for Python 3.14.7 with `qt6-main=6.9.2` also failed
  before adding the UIBCDF bindings: the current Python build requires
  `libffi>=3.7`, while the available Qt 6.9.2 dependency chain resolves only
  through older `libglib` builds requiring `libffi<3.6`. Widening the five
  UIBCDF recipe Python pins alone is therefore insufficient. The aligned Qt
  runtime and PySide family must move to a solver-compatible version or be
  rebuilt against a coherent dependency set, then pass real Qt tests on 3.14.
- The first Qt-family 6.10.1 candidate is now locally validated under
  `uibcdf/qt6-positioning-uibcdf#1`: Qt Positioning built from the exact
  upstream source commit against conda-forge `qt6-main=6.10.1`. Its Conda
  package test passed on Linux/Python 3.14.7, and an independent clean Conda
  installation loaded Positioning, PositioningQuick, and the QML plugin. The
  artifact has no Python ABI dependency and pins the exact Qt 6.10.1 runtime
  line. This removes one native package boundary.
- The first Shiboken 6.10.1 candidate is also locally validated under
  `uibcdf/shiboken6-uibcdf#1`. It ports the official 6.10.1 source while
  retaining the UIBCDF namespace. Its Linux/Python 3.14.7 Conda build and
  package test passed, and a separate clean Conda installation from the
  final local artifact imported `shiboken6_uibcdf` and ran the generator.
  Packaged metadata explicitly requires Qt 6.10.1 and `libclang13`; binary
  inspection exposed the latter as a missing direct runtime dependency in
  earlier local candidates. The published candidate branch is
  `python-3.14-qt-6.10.1` at `524745e`.
- The matching PySide6 Essentials candidate under
  `uibcdf/pyside6-essentials-uibcdf#1` is now published at `07552c0` on the
  `python-3.14-qt-6.10.1` branch. It ports official PySide 6.10.1 while
  retaining the UIBCDF namespace, and builds against that Shiboken candidate
  and conda-forge Qt 6.10.1. The final local Linux/Python 3.14 artifact
  passed its Conda package tests and an independent clean installation with
  Python 3.14.7. The durable smoke exercises QtCore, QtGui, QtWidgets,
  QtNetwork, QtQml, QtQuick, signals, Shiboken object validity, and an
  offscreen Qt event loop. This is generated-binding evidence for the
  Essentials slice, not a validated full Qt host. Safe file ownership when
  co-installed with canonical PySide6, regression coverage for 3.11–3.13,
  and other platforms remain unverified. The existing release-triggered
  Shiboken workflow still targets Python 3.13 and uploads directly to the
  main Conda label; it must not be used to publish this 3.14 candidate before
  coordinated staging.
- `uibcdf/qt6-webengine-uibcdf#1` now has a 6.10.1 candidate branch at
  `45b2209`. Its Linux package uses the official Qt WebEngine source and
  PySide wheel payloads with checked hashes, declares the native Linux
  runtime libraries, and leaves Chromium sandboxing enabled by default.
  The Conda package tests passed; a separate clean Python 3.14.7 environment
  loaded WebEngineCore and WebEngineWidgets without falling back to host
  libraries for NSS, udev, GBM, XKB, or related dependencies. That was a
  native-runtime gate, not a rendered-page test by itself.
- `uibcdf/pyside6-addons-uibcdf#1` now has the aligned 6.10.1 candidate branch
  at `e95053a`. Its reduced Addons bindings compiled and passed Conda tests
  on Linux/Python 3.14.7. An independent clean environment installed all
  five local UIBCDF Qt candidates plus `qt6-main=6.10.1`, imported
  QtPositioning, QtWebChannel, QtWebEngineCore and QtWebEngineWidgets, and
  loaded local HTML in `QWebEngineView` under Xvfb with Conda activation.
  Headless Chromium sandbox/GPU flags were applied only to that test, not to
  the package. This established a usable Qt-family smoke before running
  MolSysViewer's own optional Qt-host gate.
- MolSysViewer's real Qt integration now passes on Linux/Python 3.14.7 with
  the five aligned local 6.10.1 UIBCDF packages and no canonical `pyside6`
  installed. The existing transport test, two-generation payload test, and
  live-window test passed under Xvfb; the opt-in full-render test also passed
  with SwiftShader. The browser reached the ready state and completed a
  molecular-system render, not merely a Python import or blank HTML load.
  The same four focused tests passed in a separate environment that also had
  canonical `pyside6=6.10.1` installed. That environment's full Python suite
  passed 2,078 tests with 13 skips using 12 workers and pytest-receptor.
- Canonical PySide6 is **not** required by the intended UIBCDF-only install.
  It entered the earlier source-pair probe as a dependency of conda-forge's
  `matplotlib` metapackage; `matplotlib-base` remained after removing both.
  The UIBCDF-only environment solved without it and produced no file-overlap
  warnings. In the coexistence experiment, Conda warned about 63 shared paths
  between canonical `pyside6` and `shiboken6-uibcdf`, and 99 shared paths with
  `pyside6-essentials-uibcdf`; package manifests record 17 and 13 differing
  hashes respectively. These are CMake, tool, include, plugin, and shared-data
  paths, not a collision of the already-distinct `PySide6_uibcdf` Python
  import. `uibcdf/shiboken6-uibcdf#2` and
  `uibcdf/pyside6-essentials-uibcdf#2` own the future namespacing-or-exclusion
  decision. Coexistence is not a blocker for the validated UIBCDF-only route.
- Python 3.11–3.13 regression on the revised committed recipes and outside
  Linux, cross-platform Qt builds, staged-channel
  installation, and coordinated publication remain open. The source-pair
  development versions still do not satisfy the published MolSysMT/Viewer
  release floor, so this is feasibility evidence rather than admission of a
  versioned distribution pair.
- On 2026-09-23, Linux-64 disposable Shiboken, Essentials, and Addons
  6.10.1 variants for Python 3.11, 3.12, and 3.13 each passed their Conda
  package tests. Independent clean installations of the complete five-package
  UIBCDF-only family passed imports, Positioning checks, and a local-HTML
  WebEngine smoke under Xvfb for all three minors. Combined with the earlier
  3.14 result, this reduces the Linux regression risk but does not establish
  staged-channel or other-platform support. The three binding recipes now
  select the Python variant instead of pinning 3.14; no-download renders
  distinguish `py311`–`py314`, but the revised recipes need actual
  builds and finalized runtime checks in each cell. The MolSysMT
  `uibcdf/molsysmt#237` checkpoint holds the cross-component gate order.
- Later on 2026-09-23, the revised Shiboken, Essentials, and Addons recipes
  each built and passed Conda package tests for Linux/Python 3.12. Their
  finalized metadata pins Python and `python_abi` to 3.12, and a fresh
  five-package UIBCDF-only installation passed imports, Positioning, and
  local-HTML WebEngine loading under Xvfb. Conda recorded four artifacts
  from the indexed local channel and Addons from its local build directory;
  the latter file matches the channel copy by SHA-256. This closes one
  revised-recipe Linux cell, not the remaining minors or staging provenance.
- On 2026-09-23, the same committed Shiboken, Essentials, and Addons recipes
  also built and passed Conda package tests on Linux/Python 3.13 using 12
  build workers. Finalized metadata requires the 3.13 Python and `cp313`
  ABI variants. An independent offline environment installed Python 3.13.15,
  Qt 6.10.1, and all five local UIBCDF packages without canonical PySide6.
  Conda initially reused the Addons package cache record from its build
  directory; explicitly reinstalling the byte-identical indexed-channel
  file made all five installed records name the local channel. The ordinary
  Addons smoke and local-HTML WebEngine load under Xvfb passed. The latter
  needed a display outside the restricted sandbox; that environmental
  restriction did not indicate a package failure. This closes a second
  revised-recipe Linux cell, not staging, public support, or other platforms.
- On 2026-09-23, the revised recipes also built and passed Conda package
  tests for Linux/Python 3.14 using 12 build workers. A fresh offline
  environment installed all five exact UIBCDF artifacts from an indexed
  local channel, with matching installed-record hashes and no canonical
  PySide6. The ordinary Addons and Xvfb WebEngine smokes passed. In a
  separate environment containing the same exact local artifacts, the
  three real-Qt Viewer integration tests and the opt-in full molecular
  render passed under Xvfb. That environment uses development source
  versions of MolSysMT and Viewer, so this is local Qt/application evidence,
  not a resolver-clean, versioned Conda pair or staged-channel admission.
- Later on 2026-09-23, temporary local-only tags produced a MolSysMT ABI3
  archive and a Viewer noarch archive. An exact Linux/Python 3.14.7 Conda
  installation resolved the pair from an indexed local channel and passed
  the installed-pair validator. A PDB-text smoke exposed and then verified
  the fix for `uibcdf/molsysmt#238`: the corrected local MolSysMT `0.22.2`
  package and unchanged Viewer `0.23.2` package resolve in a second fresh
  environment without Biopython, classify and convert PDB text, and load its
  four atoms in `MolSysView`. The two existing Viewer pytest functions are
  not yet installed-package evidence because `tests/conftest.py` injects the
  source checkout, while disabling it removes their `_test_message_log`
  fixture. A direct installed smoke covers the user behavior, but an
  installed-test harness and remote staging gates were still open under
  `uibcdf/molsysviewer#82`. Neither local tag is a release-version decision.
- On 2026-09-24, an opt-in installed-package mode was added to the normal
  Viewer pytest fixtures. It omits source-path injection and requires both
  imported package directories to live in the active interpreter's
  `site-packages`; package metadata alone is insufficient because a checkout's
  `egg-info` can shadow the installed record. The two existing MolSysMT
  integration tests passed against the earlier exact local Conda pair
  (`0.22.2`/`0.23.2`) from outside both checkouts. A negative control run from
  the Viewer checkout exited 4 with the expected source-contamination error.
  This closes the local installed-test-harness gap; by itself it did not test
  newer sources or the remote staged-pair gate. The Python 3.14
  source-pair workflow now invokes these tests in installed mode and pins
  MolSysMT `8ab42b58520892d54a05222b91c116b9e9114314`. Hosted run
  `35988170629` checked out Viewer
  `b9a8c4c9c1672d6fca6fe6c5cb71cf41f8b5b845` and passed on Ubuntu,
  macOS, and Windows: each job passed the installed-pair integration step
  and the full Viewer Python suite. These were source-built pip installations,
  not immutable Conda staging packages. The local Viewer source suite passed with 12
  workers (2,082 passed, 17 skipped) outside the sandbox. Its first run in
  the restricted sandbox had 18 socket/Chromium failures, which disappeared
  unchanged outside the sandbox.
- On 2026-09-24, the updated local Python 3.14 source-pair environment passed
  the full Viewer suite with 12 workers: 2,075 passed and 17 skipped. The
  first hosted Linux/macOS/Windows source-pair run (`35968412395`) passed
  Linux (2,080 passed, 13 skipped). Windows failed at collection because a
  development benchmark imported Python's POSIX-only `resource` module at
  import time. Its current/peak working-set measurements now use the Windows
  process-memory API, with a Windows-only test. macOS reached 2,091 tests and
  had one connection-loss failure in an oversized-WebSocket test; the other
  2,090 passed or skipped. That failure is not yet classified as transient.
  Neither source-run outcome establishes a staged Conda installation.
- NGLView remains an optional integration, not a hard runtime dependency of
  MolSysViewer. A distribution-manifest test now guards its absence from both
  wheel and Conda runtime requirements. In the paired MolSysMT source tests,
  NGLView-dependent cases skip when it is absent; this does not reduce the
  core Viewer source-pair gate or imply NGLView support has been tested on
  every platform.
- The source-pair rerun `35970837689` passed Linux and macOS/Python 3.14.
  Windows passed installation and collection, but most demo-dependent tests
  failed because MolSysMT rejected the native `WindowsPath` resource
  (`uibcdf/molsysmt#241`). The MolSysMT branch now has a local fix awaiting
  Windows verification. Separate Viewer Windows failures include preview-port
  reuse and a test that assumes POSIX path spelling; they must be resolved or
  classified independently before a Windows support claim. Run
  `35972810430` pinned MolSysMT
  `e865b72ce20358c1bd33be318c170a91c18ff145`, which contains the
  native-path fix and its guard.
- The first executable Windows suite also exposed four Viewer-local
  portability defects independent of the MolSysMT path failure. The preview
  server's `SO_REUSEADDR` behavior allowed a second Windows socket to claim
  the same live port; the server now requests exclusive address use on
  Windows while retaining POSIX reuse. An argument-table audit compared
  Windows backslash paths to POSIX-style exemptions, and a digester test
  assumed POSIX spelling for a native `Path`; both now compare the intended
  platform-independent property. A foreground-CLI test used `selectors`
  on a Windows pipe and assumed POSIX SIGTERM behavior; it now waits for
  the ready line through a bounded reader thread and tests platform-appropriate
  process termination. The four affected test modules pass locally on
  Linux/Python 3.14 (132 tests), but Windows confirmation is pending. The
  Windows socket correction follows Microsoft's documented
  [`SO_EXCLUSIVEADDRUSE` behavior](https://learn.microsoft.com/en-us/windows/win32/winsock/using-so-reuseaddr-and-so-exclusiveaddruse).
- Run `35972810430`, pinned to MolSysMT's `get_form()` path fix, again passed
  Linux and macOS. Its Windows job advanced past form detection but still
  failed 55 demo-dependent tests: MolSysViewer's own molecular-system
  digester only normalized `PosixPath`, then delegated a `WindowsPath` to
  MolSysMT conversion with `skip_digestion=True`. The BCIF reader in
  `py-mmcif` expects a string and sliced the path, producing `TypeError` and
  downstream `FormatError`. The Viewer digester now normalizes native
  `PathLike` inputs once, including list/tuple inputs without mutating the
  caller's container. The output-filename digester likewise accepts native
  `Path` objects; that was a separate one-test Windows failure. Focused
  local path/demo/README tests pass, but Windows confirmation must use a
  newly pinned source-pair run. This is a trusted-delegation boundary fix,
  not an upstream change to `py-mmcif`.
- The final source-pair run pins MolSysMT
  `86dcb5d078d8cbb45c38500e452944811fc5a5bc`, whose installed-path
  guard covers PDB, H5MSM, and compressed BCIF. The Viewer branch now
  passes its local Linux/Python 3.14 full suite with 12 workers: 2,082 passed
  and 17 skipped. Hosted run `35975122014` checked out Viewer
  `88a6c75a08c3e3660b626c697183ef53c7297852` and passed all three
  jobs: each installed both exact sources, passed the MolSysMT native-path
  guard, and completed the full Viewer Python suite. This establishes the
  three-platform source-pair gate, not Conda channel admission or optional
  Windows/macOS Qt-host support.
- On 2026-09-24, the first remote staging slice used new technical coordinates
  without changing the older 0.22.0/0.23.1 release candidates. MolSysMT
  `0.22.3` ABI3 build 0 was staged for Linux x86-64 from
  `6bc7136093be1bcfff86d8600d00d630738ebd90` in run `35990161344`.
  Viewer `0.23.3` noarch build 0 was built and recipe-tested from
  `0152781987219846e5cfd0250b3e160324f9b6c5` in run `35990850975`.
  An independent channel query found its exact staging artifact with
  `python >=3.11,<3.15` and SHA-256
  `7b24b77b5bdd3dfa6cb8a7691bc23680056039dc92f05ddb8f43a60edc6993c9`.
  The exact pair resolves in a Linux/Python 3.14 dry-run. This is not an
  installed-pair result, a public package, or a decision to release those
  version numbers.

## Resolution

Pending.
