# Temporary resource lifecycle

**Owner review — 2026-10-10:** uibcdf/molsysviewer#200 implements the
component disposition requested by uibcdf/molsyssuite#104. The suite
[temporary-resource policy](https://github.com/uibcdf/molsyssuite/blob/main/devguide/temporary_resources.md)
is normative. This document records local ownership and operational contracts;
inspection, executed cleanup and historical attribution are different evidence.

## Supported operations

| Operation | Resource owner and useful lifetime | Exit and caller protection | Verification |
| --- | --- | --- | --- |
| Headless Playwright PNG | `_private.html_server.runtime_html_server` owns HTML scratch, loopback HTTP socket and serving thread; the adapter owns Chromium until the screenshot finishes | Managed directory and explicit browser/server close on success/failure. Runtime remains in the package; requested PNG remains caller-owned. Cleanup errors propagate. Port zero avoids reserve/rebind races. | Real server success/failure checks and read-only package PNG in `tests/test_headless_export_resources.py`; #228. |
| Session ZIP/H5MSM and JSON state | `session.py`, `viewer/state.py`, `interactions.py` own managed extraction/write workspaces and same-parent atomic temporary files | Context/finally cleanup; completed destination stays caller-owned. Failed atomic writes remove only their own scratch; unlink failures are visible. No directory supplied by the caller is recursively deleted. | Session rejection/bundle, state and Interactions public-completion guards. Source inspection covers error paths. |
| Loaded views/widgets/plots | View owns runtime callbacks, endpoint/binary transfers and its widgets/layout; plots own their figures | `close()`/context exit release owned resources. Test teardown closes stranded registered widgets and prints cleanup failures. Caller molecular systems remain caller-owned. | `tests/test_view_lifecycle.py`, `tests/test_trajectory_plot_lifecycle.py` and browser endpoint/popup guards. |
| Blocking preview | `tools.preview` owns its server socket until Ctrl-C/serving-loop exit | Close socket after the loop exits. Calling `shutdown()` on that same thread would deadlock. Previewed directory is never removed. | Actual subprocess Ctrl-C/socket refusal in `tests/test_preview_server.py`; #230. |
| Nonblocking preview | Ownership of the returned server is transferred to its caller | Caller invokes `shutdown()` from another thread, then `server_close()`. The managed server performs no directory cleanup. | Existing real HTTP/occupied-port preview guards. |
| Browser export fixtures | E2E suite owns a new `withFixtureWorkspace` directory; runner owns an outer workspace through all selected suites | Child processes receive TMPDIR/TMP/TEMP. HTML remains until browser verification ends. Finally removes only the created directory, after browser/server close; errors propagate. Timeout waits for suite-child exit before runner cleanup. | Real Node success/failure/caller-preservation guard in `tests/test_browser_fixture_resources.py`, plus colour/framing/controls core browser scenarios; #229. |
| Scientific E2E Python workers | Worker owns managed fixture directory until JSON-lines EOF; Node bridge owns its subprocess | Normal bridge close sends EOF, awaits exit and closes readline. The runner workspace bounds child scratch in core runs. Forced termination limits are below. | Real Interactions/composite/Studio fixtures and core browser flows. |
| Other pytest scratch | pytest owns `tmp_path` through its configured failure-analysis retention | Tests use only provided scratch; pytest controls its retention, without removing external outputs. New guards do not change global temp roots or process environment. | Existing tests and this review's focused/full runs. |
| Residency benchmark | Benchmark owns `TemporaryDirectory` for disposable storage round trips | Context removes scratch on success/failure; explicit JSON report remains caller-owned. | Existing residency benchmark guards and source inspection. |

## Development, documentation, build and qualification

Development environment `molsyssuite@uibcdf_3.14`, source checkouts and human
notebooks are deliberately persistent, shared resources. This task does not
remove them or another session's files. Qt/native browser provisioning has its
own owner; a failed launch is a failed observation, not a cleanup waiver or
passing scientific result.

`npm run build:runtime`, harness/E2E builds and Python packaging write named
repository/build outputs needed by later validation or distribution. They do not
own the containing checkout. Generated runtime and documentation embed outputs
must never be manually edited. Clean obsolete task-specific output only after
verification, preserving canonical artifacts and failure evidence still needed.

Sphinx/notebook documentation builds write caller-selected `_build`/export
paths. The documentation task owns their final review and cleanup; preview
serves without taking directory ownership. This review inspects the route and
does not build or delete the current human documentation workspace.

`devtools/build_against_staging.sh` documents the invoking task as owner of its
printed generated OUT directory; explicit output remains caller-owned. Conda
build/solver caches and disposable qualification environments belong to that
build/qualification task, through inspection and required artifact verification.
Original candidate packages, producer receipts and archive hashes remain until
their release-evidence uses end. A successful release alone does not justify
keeping the entire extracted package/environment indefinitely.

`qualify_interactions.py`, `qualify_installed_interactions.py`, release gates and
archive verifiers preserve explicitly requested outputs/evidence and do not
remove source roots or installed environments. Installed qualification must use
its own recorded interpreter/import provenance. Hosted jobs use runner-owned
workspaces and upload evidence with explicit retention (producer 7 days;
installed-pair 30 days in the current workflows). Final verification receipts
must be retained before hosted artifact expiry. Shared build/upload lifecycle
belongs to `uibcdf/action-build-and-upload-conda-packages`; this review does not
claim an audit of that provider's internal implementation.

## Bounded experimental and hard-termination limits

These are implementation exceptions, not certification of the affected routes.

- **Experimental Qt — uibcdf/molsysviewer#109.** Qt image export still uses a
  named HTML file, suppresses unlink errors and does not explicitly dispose its
  WebEngine window/timer callbacks on all outcomes. Qt standalone implicit HTML
  output may also survive a failed initialization. Owner: Viewer maintainers.
  Interim procedure: keep Qt observations in an isolated host/process, record
  the exact created HTML path, stop the host before reviewing/removing only its
  owned scratch, preserve explicit outputs. Review: 2026-11-10, or before any Qt
  stability/certification claim. Remove the exception when managed file/window/
  callback lifetimes and visible cleanup failures are protected on qualified
  native hosts. Core Playwright evidence does not qualify Qt.
- **Forced worker/host termination — uibcdf/molsysviewer#100.** SIGKILL/process
  crash cannot execute language finalizers; child descendants may outlive a
  forcibly killed suite until EOF/process shutdown. Owner: Viewer maintainers
  for local fixture/render-worker consumers. Interim procedure: use normal
  bridge close; after failure inspect the exact owned workspace and descendants,
  stop active children, preserve needed diagnostics and remove obsolete owned
  scratch. Review: 2026-11-10, or before remote-host certification. Removal
  condition: tracked process-tree shutdown/failed-start evidence on the relevant
  host. Remote rendering remains post-1.0 preview; this is not a passing GPU gate.
- **One-shot internal fixture tools.** Their printed directories are explicitly
  transferred to the invoking developer for later browser consumption. Core
  runners provide the outer managed workspace; direct consumers must record
  the printed path, retain through verification and remove it after last use.
  This caller-controlled output lifetime does not authorize deleting its parent.
  Direct one-shot producer failures before returning their path are a bounded
  compatibility-tool exception under #100: maintainers own it, callers provide
  an identified managed TMPDIR and review it after failure, review date is
  2026-11-10, and removal requires a guarded failure cleanup/ownership handoff.
  Core runner/worker contexts already bound those paths; direct one-shot failure
  cleanup is source-inspected, not certified by their normal-success checks.

## Task closeout record

The integrated 2026-10-10 review owns
`/tmp/msv-integrated-review-20261010`: test logs/JUnit, browser diagnostic logs
and tool-install evidence are retained for source review and CI comparison.
Prior `/tmp/msv-studio-coverage-20261010` retains the accepted source CI receipts;
original 0.24.1 candidate bytes keep their separate historical/staging scope.
These are useful evidence, not abandoned disposable environments. The
[review receipt](integrated_review_20261010.json) records validation identity and
explicit retained/removed paths. Removal follows the last required review, never
an age/prefix sweep. This task makes no attribution or cleanup claim for the
55 absent historical paths passed through central coordination.
