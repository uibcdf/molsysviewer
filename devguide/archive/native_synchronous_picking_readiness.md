---
summary: Preserve synchronous picks while a native asynchronous read is pending.
issue: uibcdf/molsysviewer#389
status: resolved
opened: 2026-11-14
closed: 2026-11-14
severity: medium
verification: reproduced
area: [picking, rendering, dependencies, qualification]
guard: molsysviewer/js/tests/e2e/native-picking-readiness.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Native synchronous picking readiness

Independent original-package control `816` receives 1,034 native inputs against
the original 5.13.1 tarball. With unchanged camera, point and visible sphere,
synchronous identification succeeds before and after the asynchronous read,
but returns nothing while that read is pending. WebGL2 is present and the
camera is stationary. No MolSysViewer import/adapter or synthetic event is
used. The failed positive setup `815` incorrectly paused manual drawing and
remains separate. Both preserve inputs and retire their processes.

`asyncIdentify` clears `dirty` through rendering and makes its buffers unready.
`identify` reads only when dirty; unready buffers refuse IDs. The native click
helper uses synchronous identification. This is a concrete relevant mechanism,
not proof of the exact original #388 event sequence.

The clean upstream checkout is current at `dabbf29f` on master. Its new
graphics/workspace architecture handles pending clicks explicitly; `7aa232cc`
documents that a click must not resolve to nothing. That implementation is
not the published pinned 5.13.1 or an adopted v6 migration.

Receive a narrow version/source-gated repair through ordinary build routes,
original-versus-repaired real GPU controls and independent-view/disposal
controls. Preserve actual clicks, hover/marker assertions and installed native
bytes. Track removal against a qualified native replacement. The complete
four-page, 359-issue history has no equivalent report. Parent #372/#369/#315.

## Source resolution — 2026-11-14

The build adapter now admits only exact 5.13.1 source hashes and changes the
synchronous read condition to `dirty || !buffers.ready`. It does not edit the
installed provider or change a selection API. Both dependent native files are
checked before and during bundling. All three normal build routes retain the
same adapter and reject changed inputs. Future dependency qualification under
#115 must receive an equivalent native guarantee before removing this repair.

Matched original control `819` uses the exact same native-only scenario as the
mandatory repaired core entry. Both independent plugins return no synchronous
hit during a pending read with original bytes; their positive before/after
controls, camera and retained peer remain correct. Repaired `822` passes the
same before/during/resolved/after identities and disposal controls on real
WebGL2. Original 1,034 consumed files and repaired 6,356 installed JS/declaration
files match their original artifact; only the reviewed build output changes.

Build/type, 491 JS cases and 494 scoped Python cases pass in `818`; native
context-menu passes in `820` before that attempt fails a missing export of the
new helper. Explicitly exporting it from the IIFE harness fixes the test setup
(`821`); `822` then passes both complete picking and coordinate/edit suites.
Both failed setups (`815`, `820`) and sandbox launch (`817`) remain evidence.
No deadline, scientific predicate or click action is weakened. Full covering
CI and installed candidate acceptance remain owned by #372; this source
resolution does not establish the original #388 event sequence.
