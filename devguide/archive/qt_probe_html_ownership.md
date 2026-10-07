---
summary: Parent-owned HTML fixtures survive asynchronous Qt reads and clean after child completion or termination.
issue: uibcdf/molsysviewer#178
status: resolved
opened: 2026-10-07
closed: 2026-10-07
severity: medium
verification: reproduced
area: [testing, tooling]
guard: tests/test_qt_probe_resources.py
normative:
blocked_by: []
supersedes: []
---

# Disposable Qt probe HTML ownership

**Done:** both child HTML fixtures have parent-managed lifetimes and real Qt
cleanup regressions. Shared coordination is uibcdf/molsyssuite#104.

## What

The transport and two-generation child probes in tests/test_standalone.py use
NamedTemporaryFile(delete=False), with no unlink on any exit. The original
inspection used 5ef54ab6df99fce4c786ac9a0046f7fd08f55627. Fetched repair baseline
8b08e1c4ccf1f9602f568b9fe6cf82d639df1be8 retains both leaks. Async Qt reads need
the HTML to remain present until the child completes or is terminated.

## How

The independently usable tests/_qt_probe.py::run_qt_html_probe owns a managed
TemporaryDirectory and passes one HTML path to the cold child interpreter.
Each actual probe writes its unchanged HTML there. Capture settings, 90-second
timeouts, curated environment, event processing, generation behavior and original
assertions remain intact. The helper removes the directory only after the child
returns or subprocess.run kills/reaps a timed-out child. Removal errors propagate;
caller environment and retained evidence are outside this disposable directory.
This is local test infrastructure outside the installed Viewer API.

The build_against_staging.sh header now documents output ownership and closeout.
Its printed OUT belongs to the invoking release/qualification task, including an
implicit directory. Original candidates/evidence are retained through installed
qualification, promotion/public verification or failure diagnosis. Their owner
records OUT and removes obsolete output after checking active/human work.
Caller-supplied output remains caller-controlled; no exit cleanup or build change.

## Why and executed evidence

Eight regressions invoke the actual parent tests and actual Qt/bridge children,
without substituting Qt or molecular calculations. They exercise each probe's
normal transport, controlled exception after HTML creation, real timeout with
child reaping, and observable removal error after child completion. They protect
caller-owned receipt retention and keep the HTML through real asynchronous loads.
All eight fail at the original source: six retained HTML files and two missing
removal errors. They pass after repair; both original Qt observations also pass.
Together with reporting checks, 201 selected tests pass in 40.54 seconds on
molsyssuite@uibcdf_3.14, Python 3.14.7. Whole-repository Ruff, dependency metadata,
report indexes and bash -n pass.

The first sandboxed attempt fails before resource assertions because Qt's internal
socket shutdown is denied. The same selection outside that sandbox reproduces the
actual eight lifecycle failures; the corrected outside-sandbox run passes. No Qt
version, resource-path workaround, environment reinstall or rendering change.

## What was refuted

Closing a NamedTemporaryFile handle does not unlink it. Early child deletion can
race asynchronous loads; child-only cleanup cannot survive a killed child.
Standard parent ownership suffices. A whole-machine cleaner or deletion of retained
build candidates would violate task ownership. The initial sandbox failure is a
host restriction, not scientific or Qt-product evidence.

## Resolution and guard

The module guard is addressable and relevant: all eight cases fail before this
repair and pass afterward with real child execution. Original transport/payload
observations remain green. The helper documents its path/capture/timeout/ownership
contract and is reused by both parents. Archive/index move together. Exact native
administrative evidence and task resource closeout are delivered to this issue
and the central #104 receipt after execution.

## Scope and deferred evidence

Only local test-resource ownership and build-output lifecycle documentation change.
No installed runtime API, canonical guide, frontend/generated bundle, public package
bytes, release decision or artifact qualification changes. The real offscreen
probes establish transport/fixture lifetime, not framebuffer correctness or a
visible GPU observation. Full scientific suites and browser matrices remain
postponed by the principal maintainer's decision.

Use the authorized internal skip/manual route for this source checkpoint: local
resource/Qt/reporting checks and exact native policy/publication controls qualify
the focused repair. Full CI/E2E debt remains owned by the component developers
(Diego/Liliana) under uibcdf/molsysviewer#93, with existing scheduled/manual CI.yaml
and CI_e2e.yaml recovery routes. Administrative evidence does not clear that debt
or qualify a new release. All full tool/retrospective reviews keep #104 partial.

## Active-owner integration checkpoint — 2026-10-07

While preparing this local repair, origin/main advanced to 484686524d4b928fddc96b98db7e01e3821edbc6 with existing
public Windows, installed-fixture, E2E-worker and box qualification closures.
Integrate those documentation changes; preserve all archive-index entries.
The helper, both parent/child probes, lifecycle guard and build script bytes are
unchanged from the measured local repair, so the eight lifecycle cases and two
original real-Qt results remain applicable. The earlier reporting counts describe
their dated inputs. All 180 current integrated reporting checks, dependency audit,
whole-repository Ruff, generated queue indexes and bash syntax check also pass.
The maintained flat archive receives its customary one-line index entry; the
local generator manages queue indexes. Final exact-head administrative evidence
is retained separately from postponed scientific/full-browser source evidence.
