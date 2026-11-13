---
summary: Separate public-default capture from deliberately delayed Jupyter queries.
issue: uibcdf/molsysviewer#381
status: resolved
opened: 2026-11-13
closed: 2026-11-13
severity: medium
verification: measured
area: [jupyter, testing, capture]
guard: tests/test_jupyter_live_capture.py::test_live_jupyter_work_files
normative:
blocked_by: []
supersedes: []
---

# Resolved: moving Jupyter fixture deadline budget

Resolved in source and actual-host receiving: two healthy Python default
captures complement all six explicitly delayed scientific captures. Public
defaults, scientific assertions and rendering/playback quality are unchanged.

Receive the default public Python state/session deadline separately from the
six existing delayed-query controls. Keep genuine science, two post-request
frame changes, exact native-draw/file equivalence, source preservation and
cancellation/late-write assertions. Deliberately delayed Python calls use an
explicit bounded timeout; healthy default calls omit that argument. This adds
two moving cases, without changing any public default, playback/quality setting
or production calculation.

Original full receiving `733`/`737` fails the moving Python state save;
unchanged product code completes all six moving cases in `736`. In `737`,
the fixture holds scientific requests for 3,817.6 ms of the request's
4,999.93 ms, leaving about 1.18 seconds for genuine replies, geometry and a
completed draw. Current-frame dependencies first become coherent about
5.64 seconds after capture starts. All three attempts retain unchanged inputs,
their native outcomes and clean own-process teardown, without resource stops.
This identifies an adverse fixture budget assumption, not an established
broken production timeout or upstream regression. Keep the original failures.

Closed #343/#344 own the earlier transport/presentation corrections. The full
pre-report all-state inventory contains four pages/351 issues excluding PRs;
no equivalent focused fixture report was identified. Record actual kernel
module/extension origins and hashes and private hold timings. Ordinary offline
validation must reject losing either scenario class, changing its requested
deadline or dropping the original scientific assertions. Complete native
eight-case receiving is required before closure; an unselected skip is not it.

## Resolution

`738` passes 28 offline controls, including nine independently introduced
scope/deadline/identity/science failures that the shared validator rejects.
Its one unselected host skip and two deselected native tests are not native
acceptance. The owner CLI validates the complete report after a native exit 0,
and the selected pytest guard uses that same contract.
Final `740` passes 472 owner/reporting controls, Ruff, formatting, JavaScript
syntax and queue indexes; its optional-host skip/deselections retain that same
limited meaning.

Canonical actual-Jupyter `739` receives the entire eight-moving-case scope:
healthy Python state/session omit `timeout` and request 4,999.94/4,999.95 ms;
the six delayed cases explicitly request about 9,999.9 ms and preserve two
genuine post-request frame changes. All eight compare real completed draws
with independently restored file values and unchanged source coordinates.
The full guard also receives six stopped roundtrips, six strong restores,
four Studio cases, cancellation and autonomous expiry without late writes.
Native browser/owner exits are 0, all selected inputs are unchanged and cleanup
has no survivor/error or resource stop. Actual kernel module/extension origins
and hashes are recorded, including the qualified Rust bytes `4ffb82e4…`.

Receiving takes 232 seconds within the former 240-second aggregate. The full
eight-case profile now has a separate 300-second aggregate budget; other
profiles retain 240 seconds and per-operation defaults remain five seconds.
That aggregate-only adjustment does not relabel the original input snapshot.
The 733/737 failures and 736 six-case pass remain preserved as their own
scopes. New exact-head/platform/installed and postponed human acceptance still
belong to #372/#315.
