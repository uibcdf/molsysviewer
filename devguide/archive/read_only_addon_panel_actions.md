---
summary: Admit declared read-only actions from mounted addon panels during pending scene synchronization.
issue: uibcdf/molsysviewer#304
status: resolved
opened: 2026-11-06
closed: 2026-11-10
verification: reproduced
area: [addons, synchronization, api]
guard: molsysviewer/js/tests/e2e/coordinate-edits.e2e.ts
normative: docs/content/developer/addons.md
blocked_by: []
supersedes: []
---

# Declared read-only addon panel requests — resolved

Twenty-two current Python controls and the actual coordinate-edits browser guard receive mounted native reads, old-scene inertness and exact DOM restoration. Prior actual Jupyter/popup and hosted 177e19a8 scopes are retained. See the [host integration receipt](../host_integration_closeout_20261110.json). Covering hosted/installed and postponed human acceptance remain separate under #264/#315. The sections below retain their original checkpoint scopes.

## What

The initial current-primary scientific reader was available during pending
managed edits, but the host dropped all addon panel requests before dispatch. Chemistry's two
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

At the first transport checkpoint, the recovery sheet still covered the scene
and made underlying Studio controls inert. That server-only slice did not
qualify pointer/keyboard access; the implemented frontend receiving below
now addresses that required scope. Broader regression found a
headless context-query compatibility regression in the first draft; it is
corrected by preserving the existing empty-context query without admitting
actions from an unmounted widget.

The broader managed-edit/addon/endpoint/public-API regression now passes 111
cases in 9.40 s, with the one unchanged optional legacy-entry-point skip.
Chemistry's expanded 42-case receiving passes in 10.36 s, adding explicit and
associated chemical states, nonconsecutive structure contexts, ambiguous
reference coverage and scene-membership invalidation without a molecular edit.

That initial checkpoint left actual Jupyter receiving and hosted/integration
qualification pending. Later receiving is recorded below. Human visible-host acceptance
is explicitly postponed. The source change does not qualify an installed
artifact or authorize either 1.0 publication.

## Broader source qualification — 2026-11-06

Consumer PR #543 delivers its source at
`9739f8dee1f8c71ae4e0043a19eb67acab8939ad`, pinned to host 63e79096. The
[Chemistry receipt](../molsysmt_chemistry_receiving_20261106.json) records eight
actual synchronized Jupyter/Mol*/popup scenarios (55 steps) alongside 363
native/panel cases. That earlier synchronized receiving did not qualify pending-state
pointer/keyboard admission. The follow-up below supplies that evidence.

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

## Interactive reader recovery — 2026-11-06

The [new receiving record](../molsysmt_pending_reader_receiving_20261106.json)
identifies the host and provider inputs. Server-declared mounted reader content
is temporarily placed in the recovery sheet during pending/sync_failed, then
returned to its original Studio parent. It retains its widget, CSS, DOM and
handlers. Original per-element inert states are restored; expired notices are
not recreated. Native input and reader handlers receive their events while
old-scene shortcuts and pointer interaction stay isolated. No navigation,
trait-write, presentation or new-widget exemption is added.

Chemistry cancels stale in-flight requests on synchronization transitions and
requests fresh data only in admitted states. The first real UI test exposed a
permanent busy state after an editing-stage refresh with no promised reply;
the provider lifecycle correction preserves native scientific methods/results.

The full JS unit collection passes 339 cases; Python host/addon/managed-edit
regression passes 94 with one unchanged legacy-entry skip. The permanent
coordinate-edits browser entry now reads a native new box in nm while proving
that the displayed Mol* cell is still old, rejects undeclared actions and checks
real keys, same-DOM restoration and original inert values. All eight original
synchronized Jupyter scenarios pass in the nine-case collection; the new case
failed on a bootstrap navigation selector. After correcting that guard, the
pending case passes separately (eight steps, 50.40 s) in embedded Jupyter,
canvas popup and detached Studio. This is retained eight-plus-one receiving,
not a newly executed single green complete run. Original failures and unchanged
scientific assertions are recorded.

Frontend source and actual automated pointer/keyboard receiving are delivered;
exact-head hosted gates and owner integration remain pending, so the report
stays partial. Human visible-host review remains postponed and installed
packages are separate. Historical hosted controls failure 42206567233 is owned
by #305; a passing local mirror guard does not explain or erase it.
