---
summary: Native Qt result-window cleanup can abort after functional construction checks finish.
issue: uibcdf/molsysviewer#351
status: resolved
opened: 2026-11-10
closed: 2026-11-10
severity: medium
verification: reproduced
area: [qt, lifecycle, independent-views]
guard: tests/test_qt_presentations.py::test_rendered_independent_result_window_disposal
normative: docs/content/developer/standalone_surfaces.md
blocked_by: []
supersedes: []
---

# Native result-window teardown

**Resolved in source, with actual native disposal receiving.** Preserve the original failed Qt guard despite
its six completed functional assertions. The host remains experimental; this
finding does not change the existing release scope or authorize publication.

## Observations

During D6.5 receiving, the new native construction guard starts from an empty
View, opens and geometrically receives an independent peptide window, adopts
an independent water cell, receives seeded ion placement and a declared
assembly, then solvates an explicitly prepared solute. All six assertions and
the final functional report complete. Closing presentation records and the
primary window, followed by draining `DeferredDelete`, aborts the process with
native exit -6. The Python frame is `QCoreApplication.sendPostedEvents`; the
native stack reaches Qt WebEngine's fatal cleanup path. The message is
`Failed to restore OpenGL context after clean-up.`

The retained 166 invocation uses core checkpoint `6c2b69ba` (runtime
`b9f3be0127b1fd48220cf400471044bd0b65dbe3`) and an uncommitted construction
contribution based on native `6bd879bda202feee372b25a61734ee13ee7928ac` and
physical-recipe PR #696. Backend bytes are the received canonical
`58653b1d477be36017d2bc721dafe6e85a508e2325fa3226ccf26c61d449d6e5`.
Inputs stay unchanged. With 2 CPU/6 GiB, summed owned RSS peaks near 2.24 GiB;
there are no surviving owned processes or resource-stop events.

An earlier invocation 164 aborts during exception cleanup. Its newly written
fixture tried an unavailable native assembly setter. The independent probe
reproduces that separate limitation without Qt; it is uibcdf/molsysmt#697.
Correcting the fixture to the public Structures constructor does not resolve
the later abort after successful functional checks. Preserve both failures.

Private evidence is under the approved robustness workspace's
`next-ten-20261109/166-construction-supported-inputs`: invocation/input hashes,
JUnit, full native/Python stack, functional report and native screenshot.
This is source receiving, not installed or human acceptance.

## Investigation and acceptance

The [official Qt WebEngine 6.11 source](https://github.com/qt/qtwebengine/blob/6.11/src/core/compositor/native_skia_output_device_opengl.cpp)
shows a cleanup scope that temporarily binds a creation context and attempts
to restore the previously current context/surface. That explains the fatal
message's mechanism; it does not establish whether our disposal ordering or
the Qt/provider lifecycle is responsible. Profiles must also outlive their
pages; retain that [Qt ownership boundary](https://doc.qt.io/qt-6.11/qwebengineprofile.html).

Isolate visible and unpresented result pages, source/result close order,
replacement draws, application shutdown and exception cleanup on an actual
qualified display. Check destruction and current-context/surface observations
without altering rendering merely to obtain a pass. A correction must preserve
independent owners and actual cleanup, with a failing native regression first.
Removing deferred deletion, disabling GPU, switching to offscreen or ignoring
the process exit does not receive this boundary. No external upstream report
is authorized by the internal finding alone.

## Resolution — 2026-11-10

Keep the native surface alive through actual page destruction and then profile destruction; queue final window close after the child destructor. QApplication retains hosts until retirement. Registered results and failed initializer runtimes share private ordered disposal. The real Molstar guard receives visible/unpresented results, replacement draws and initializer failure, then verifies six page/profile pairs and five result windows are destroyed, temporary shells are gone and no graphics leak/fatal message occurs. The addon construction guard independently passes six checks and complete retirement. The previous production baseline fails the strict original regression on leaked graphics resources. The [receipt](../qt_independent_disposal_receiving_20261110.json) retains failures, source hashes and scope. The 101 affected headless controls also pass. Linux native receiving is separate from installed, other-platform and postponed human qualification; Qt remains experimental.
