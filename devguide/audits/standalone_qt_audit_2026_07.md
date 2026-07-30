# Standalone Qt audit — 2026-07

**Status:** closed. Findings Q1-Q5 were implemented and mutation-tested.

## Scope and method

This audit reviews `molsysviewer/standalone_qt/` as a deployment path. It does not
change product code. The review combined source inspection, the existing Qt test
suite, isolated error probes, a 95,000-atom transport measurement, and a real
offscreen launch through the installed `molsysviewer-qt` entry point.

The premise that the directory had zero tests is obsolete. `tests/test_standalone.py`
currently contains 26 tests. On the audited host, 24 passed and two were skipped:
the real URL-scheme transport smoke ran and passed; the live window/render checks
were skipped because the host has no `DISPLAY` and the opt-in GPU test was not
enabled.

## Component map

### `view_channel.py` — widget compatibility shim

`QtViewChannel` implements the subset of the widget surface used during normal live
operation: `send`, `on_msg`, `initial_messages`, mutable configuration attributes,
and a layout object with size attributes. Outgoing messages use `QtMessageBridge`;
incoming product events are delivered with the AnyWidget callback signature
`(widget, content, buffers)`.

The shim is faithful for the normal live path exercised by `core.py`: message send,
pre-ready accumulation, ready notification, interactions, and movie events. It is
not a complete substitute for the widget protocol:

- `_Layout` has no `get_state()` or `model_id`.
- `get_state()` always returns an empty dictionary.
- `on_msg()` does not implement the widget's callback-removal form.
- `buffers` passed to `send()` are ignored.
- configuration and layout attributes are inert; assigning them does not update the
  Qt shell or native window.

The missing state/layout protocol is observable through shared public code. Calling
`view._build_standalone_html()` on a `MolSysView` backed by `QtViewChannel` raises
`AttributeError: '_Layout' object has no attribute 'get_state'`. The Qt menu avoids
this by constructing a separate export view, but the claim that the same
`MolSysView` supports the complete shared surface is therefore too broad.

`initial_messages` also has narrower semantics than the AnyWidget trait. It assumes
that every assignment is the previous list plus an appended suffix. Replacing or
shrinking the list does not forward the replacement. That is correct for the current
pre-ready append path, but not for arbitrary trait-compatible assignment, including
the assignments performed by the shared standalone export path. The live queue and
the serializable widget state should be treated as separate contracts.

### `utils.py` — mostly Qt plumbing, with a small legacy fallback seam

The 897 lines are not a second molecular viewer implementation. They divide into:

- Qt/Conda environment discovery and imports;
- shell state, recent-source, window, and status-bar plumbing;
- `QtMessageBridge`, custom URL schemes, payload serving, queueing, acknowledgements,
  timeouts, coalescing, and generation handling;
- thin orchestration that delegates molecular work to `MolSysView.load()`,
  `_build_export_messages()`, and the shared export API.

The main duplication risk is the fallback used when a webview has no persistent
`_molsysviewer_view`: `_build_qt_live_messages()` creates/resolves another view and
replays its export messages. The production application installs a persistent view,
so this is legacy compatibility rather than the primary path. `_reload_html_in_view`
is exported but has no caller. Several load helpers still carry unused `QUrl`,
`html_path`, and title arguments from the static-HTML model. These are cleanup debt,
not duplicated scientific logic.

### `application.py` — assembly and native integration

This module creates the Qt application/window/webview, installs both custom schemes,
constructs the persistent `MolSysView` and `QtViewChannel`, forwards context-menu
events, attaches menus, and initiates the first live load. Add-on preparation occurs
while building the shell HTML and updates the global add-on registry before the
persistent view is created, so the persistent view sees that registry.

The native context-menu callback catches every exception and discards it. A failure
to build or show the menu is therefore invisible to both the user and diagnostics.

### `menus.py` — Qt UI wiring

This is native menu and dialog plumbing. Molecular operations delegate to the
persistent view or shared helpers. Errors from user-initiated load/export operations
are generally converted into a status-bar message and message box. It is lower risk
than the transport, although its broad callback surface is mostly covered with fake
Qt objects rather than a real window.

### `main.py` — console entry point

The supported entry point is the installed `molsysviewer-qt` script. On the audited
host,

```text
QT_QPA_PLATFORM=offscreen QTWEBENGINE_DISABLE_SANDBOX=1 \
  molsysviewer-qt --no-exec --output /tmp/molsysviewer-qt-audit.html
```

returned successfully and created the HTML shell. Qt reported that it could not
create an OpenGL/Vulkan context, as expected without a display, so this proves real
application construction but not rendering. Running
`python -m molsysviewer.standalone_qt.main` does not invoke `main()` because the
module has no `if __name__ == "__main__"` block; this is not currently the documented
packaging entry point.

## Error-path findings

### Q1 — Product-event failures are silently swallowed (high)

`QtMessageBridge._forward_to_view()` catches `Exception` from `event_sink` and does
nothing. An isolated probe installed a sink that raises `RuntimeError`; the bridge
returned normally, emitted no status, and retained no diagnostic. Consequently, a
bug in `MolSysView._handle_frontend_event()` can disable an interaction, movie event,
or runtime update only in Qt while leaving the shell apparently healthy. This also
violates the repository's SMonitor rule that diagnostic emission failures must not
be silently discarded.

### Q2 — Missing page/bridge states can stall without a terminal signal (high)

Constructing `QtViewChannel(None)` fails loudly but only as an incidental
`AttributeError`. More importantly, if `QtMessageBridge._run_javascript()` finds no
usable page, it puts the entry back at the front of the queue and returns without
arming another retry or reporting a status. The queue can remain permanently stalled
while `ready` stays true. A JavaScript exception retries indefinitely every 50 ms;
there is no retry ceiling or terminal bridge state.

### Q3 — Malformed direct events are not validated at the bridge boundary (medium)

The URL decoder correctly rejects invalid JSON, non-dictionaries, and dictionaries
without a string `event`. However, `QtMessageBridge.handle_frontend_event()` and
`QtViewChannel._dispatch_event()` assume a dictionary. Passing a string raises
`AttributeError`. Through the URL scheme this is filtered; through an alternate or
future bridge producer it is not. The scheme handler replies `{"ok": true}` even
when a malformed event was discarded, leaving no diagnostic trace.

### Q4 — Timeout/retry policy does not guarantee delivery (medium)

The developer documentation says no message is silently dropped. In practice, a
message timeout removes the inflight entry, reports status, and advances the queue;
it does not retry. Conversely, a synchronous `runJavaScript` failure can retry
without limit. The implementation has status feedback, so timeout loss is not fully
silent, but the documented delivery guarantee and the actual policy differ.

### Q5 — Shell persistence errors are deliberately invisible (low/medium)

Loading malformed shell state falls back safely, and failure to save shell state is
ignored. These are non-critical paths, but no warning distinguishes an intentionally
fresh session from persistence failure. Native context-menu errors are similarly
discarded.

## `initial_messages` performance

The probe used one 95,000-atom payload with 2,257,847 serialized bytes:

| operation | observed time |
|---|---:|
| first `QtViewChannel.initial_messages` assignment | 64.4 ms |
| direct `QtMessageBridge.send` of the same message | 68.7 ms |
| cumulative append of one small message | 0.03 ms |

The shim does not reproduce the old Jupyter trait toll. The measurable cost is the
required JSON serialization/materialization of a large payload in the bridge; the
channel adds no meaningful overhead. Only the newly appended suffix is forwarded.

## Existing test coverage and gaps

Existing tests already protect much more than the backlog stated:

- fake-Qt construction, menus, load errors, persistence, recent sources, and CLI;
- queueing, large payload references, generations, progress, and transport events;
- `QtViewChannel` send, cumulative initial messages, close, interaction, and movie;
- real Qt URL-scheme transport in an offscreen subprocess;
- optional real-window and GPU/render tests.

The principal gaps are behavioral error contracts, not line coverage:

1. a failing view callback must become an observable diagnostic;
2. page/bridge disappearance must have an explicit terminal or bounded-retry policy;
3. malformed direct events must be rejected at the bridge boundary;
4. replacement/shrink semantics of `initial_messages` must be specified and tested,
   or the shim must stop claiming trait equivalence;
5. public export from the persistent Qt-backed view must either work or fail with a
   documented, intentional exception;
6. one real WebGL render remains necessary before declaring the deployed standalone
   visually validated.

## Recommended next work

1. **Define the transport error contract before changing code.** Decide which failures
   are retryable, the retry ceiling, what becomes a status-bar error, and what is
   emitted through SMonitor. Add focused tests for Q1–Q3.
2. **Resolve the widget-state boundary.** Prefer separating live transport from HTML
   export state rather than making a Qt shim emulate all of ipywidgets accidentally.
   Then test the supported public export path explicitly.
3. **Keep and strengthen the real transport smoke.** PySide/QtWebEngine absence should
   be visible in the deployment test matrix rather than silently reducing coverage.
4. **Run the existing opt-in full-render test on the supported Qt workstation or a
   dedicated WebGL-capable job.** This host cannot establish that rendering works.
5. **After contracts are guarded, remove legacy fallback residue** (`_reload_html_in_view`,
   unused static-path parameters, and possibly `_build_qt_live_messages`) only if no
   supported embedding uses it.

## Verdict

The Qt standalone is not an untested 1,811-line blind spot. Its live transport has a
substantial fake-based suite and one real Qt transport smoke, and the installed entry
point constructs successfully on this host. `utils.py` is predominantly necessary Qt
plumbing rather than dangerous duplication.

It is nevertheless not ready to call fully hardened. The highest-risk gap is that
exceptions crossing from the Qt bridge into the shared `MolSysView` disappear without
diagnostics. The second is an underspecified failure/retry state machine that can
either stall or retry indefinitely. Actual Mol*/WebGL rendering was not validated on
this host. These are focused, testable debts; they do not justify a broad rewrite or
dozens of superficial menu tests.
