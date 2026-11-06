---
summary: Admit declared read-only actions from mounted addon panels during pending scene synchronization.
issue: uibcdf/molsysviewer#304
status: partial
opened: 2026-11-06
closed:
verification: reproduced
area: [addons, synchronization, api]
guard: tests/test_addon_read_only_actions.py
normative: docs/content/developer/addons.md
blocked_by: []
supersedes: []
---

# Declared read-only addon panel requests

## What

The current-primary scientific reader is available during pending managed edits,
but the host drops all addon panel requests before dispatch. Chemistry's two
source receiving cases observed no response to an otherwise valid read. This
is a missing admission contract, separate from #297's outgoing metadata and
#302's preparation-only scene readback. The complete 302-record board inventory
was inspected before filing; neither closed issue covers incoming reader actions.

## Contract and implementation

`AddonPanelWidget.read_only_actions` defaults to an empty tuple. A provider
declares exact action IDs; the host accepts only `type='action'`, a mapping
payload and the active addon/panel/authenticated endpoint. Direct widget comms
use the same classification. Admission applies only in `pending`/`sync_failed`.
Editing, syncing, uncertain, closed, unmounted and foreign endpoints retain
their guards. Navigation, viewer-context queries and result presentation gain
no exemption.

The handler executes under the existing serialization lock. Its narrow context
admits that widget's exact `handle_action` call, including normal digestion;
nested scene methods and another action ID still fail before digestion, even
with `skip_digestion=True`. No general internal-edit context is granted. The
provider is responsible for reader semantics, current-primary selection and
bounded outputs; trusted addon Python is not a security sandbox. Raw native
writes are not automatically observed.

## Evidence and remaining work

Twenty-three focused host/metadata cases pass in 4.74 s. They cover actual
native demo reads, retained pending state, both endpoint types, direct transport,
forged/late requests and nested guard/context cleanup. All 34 initial Chemistry
consumer cases pass with the new route in 7.37 s, including safe current-primary
reads and rejection of old scene memberships during pending synchronization.
The original consumer two-case failure and an initial test-import collection
error are retained as local diagnostics; neither is relabelled as passing.

The canvas recovery sheet still covers the scene and makes underlying Studio
controls inert. This server route does not yet qualify pointer/keyboard access
to a read-only task while the scene is paused. Frontend admission and its
actual Jupyter proof remain required work under this issue; the transport slice
does not close it or silently defer that scope. Broader regression found a
headless context-query compatibility regression in the first draft; it is
corrected by preserving the existing empty-context query without admitting
actions from an unmounted widget.

The broader managed-edit/addon/endpoint/public-API regression now passes 111
cases in 9.40 s, with the one unchanged optional legacy-entry-point skip.
Chemistry's expanded 42-case receiving passes in 10.36 s, adding explicit and
associated chemical states, nonconsecutive structure contexts, ambiguous
reference coverage and scene-membership invalidation without a molecular edit.

Actual Jupyter receiving, exact-source hosted CI and
the final integration checkpoint remain pending. Human visible-host acceptance
is explicitly postponed. The source change does not qualify an installed
artifact or authorize either 1.0 publication.

## Broader source qualification — 2026-11-06

The full non-Qt selection initially passed 3,451 cases, with 24 failures and six
setup errors in the restricted sandbox (531.24 s; 21 skips, 15 Qt deselections).
The seven affected modules exercised loopback servers, Chromium and nested Node
coverage processes. With approved host permissions and unchanged production
inputs, all those modules pass: 64 passed, one unchanged GPU-environment skip
in 59.89 s. Retain both runs and their overlapping selections; this is recovery
of the failed modules, not a newly executed single green full-suite run. The
Node coverage probe also passes under the same Node version; no version or
coverage-assertion workaround was introduced.

The synchronized Chemistry flow passes seven actual Jupyter/Mol*/popup steps
in 38.85 s. It verifies native arrays, chemical domains, scene objects and the
molecular revision. Its initial pre-render scene lacked a camera snapshot;
the only final document difference is the expected first frontend camera
record, with every object, structure and playback setting unchanged. This
receiving does not exercise pointer access through the pending-state sheet.
