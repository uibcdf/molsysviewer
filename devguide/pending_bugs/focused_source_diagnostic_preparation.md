---
summary: Keep focused source diagnostics behind audited installation and built browser prerequisites.
issue: uibcdf/molsysviewer#399
status: active
opened: 2026-11-16
closed:
severity: medium
verification: reproduced
area: [ci, jupyter, diagnostics]
guard: tests/test_source_workflow_coverage.py
normative:
blocked_by: []
supersedes: []
---

# Focused source diagnostic preparation

Run [43786553755](https://github.com/uibcdf/molsysviewer/actions/runs/43786553755)
at MolSysViewer `391e004d` / MolSysMT `b8c798474` fails its dependency audit
because the later prolonged consumer installs the provider again. That
consumer also passes `-n0` without pytest-xdist: usage exit 4 executes no
cases. The editable source installation now belongs before the audit, and
the one explicit case uses pytest's default sequential execution.

Successor `43790196548`, at `5f6fc2a5`, passes that audit but fails the
unchanged installed Rust validator: `installed MolSysMT distribution is
editable`. No browser/Jupyter consumer starts, which receives the new
prerequisite fence. The source receiver needs an in-place native extension;
ordinary consumers still require a non-editable installed distribution.
Prepare the former through the same source's editable build, then finish the
initial installation with the ordinary non-editable package before auditing.
Keep the existing installed validator, export manifest, native smoke and
prefix checks unchanged. This is source-build diagnostic preparation, not a
Conda artifact or installed-pair qualification.

The browser build and four focused suites were skipped. A later
`!cancelled()` actual-Jupyter consumer nevertheless ran: six stopped
capture/restore cases, including all four Studio cases, completed before a
generic `Error`. Its retained phase is stale: moving setup reads the generated
harness before changing the phase. A missing harness is consistent with the
skipped build; the original safe receipt does not preserve the actual exception,
so this is not an established explanation or a new Studio save defect.

Independent consumers now require explicit successful audit, browser build
and browser checks. They may still collect independent evidence after an
unrelated browser assertion fails. Moving setup names its phase before any
I/O, retains the original exception privately, and exports only the closed
`moving_harness_missing` code for that exact missing-file boundary. A real
Node missing-file regression checks the phase, original ENOENT and private
path retention; the safe-summary tests reject arbitrary or misattributed
codes. No raw kernel messages, paths, tokens or payloads are added to uploads.

The [four-issue receipt](../residual_four_issues_receiving_20261116.json)
retains the original terminal failure and exact artifact digest. Offline
checks and one corrected bounded hosted dispatch are required before closure.
This does not close #305/#321/#325/#354, qualify an installed pair, or authorize
tags, packages or publication.

Run `43791283994`, at `84da6b60`, receives the corrected installation/audit,
unchanged installed Rust validation, 491 JS cases and TypeScript. The complete
actual-Jupyter entry passes six stopped/restored and eight moving captures,
with all 18 processes retired. Context-menu passes. Controls receiving opens
the actual popup menu, then the newly added test waits for an FPS input that
compact mode intentionally does not render. Observe its real controller's
applied FPS instead. The following mirror/plot suites are not reached by the
fail-fast runner; give the four independent diagnostic owners separate failing
steps while retaining the full default core lane unchanged.

The prolonged owner case separately fails before server/kernel startup on a
fixed missing `/usr/bin/node`, reported to MolSysMT #767. Its CLI accepts an
explicit Node choice but the pytest wrapper cannot forward one. That is not
a recurrence of the historical pre-save frame assertion. Both original ZIPs
are downloaded and verified against GitHub's digests; the failed overall run
is retained alongside its successful Jupyter scope.

MolSysMT publishes portable Node receiving in `4b0b1f8a`; independent consumer
`961` passes 94 controls plus the actual selected Node-22 version probe. Local
complete controls and scientific mirror now pass in `959`; the plot separately
passes isolated `960`, retaining the earlier startup failure. The next bounded
hosted checkpoint pins that published receiver, forwards the chosen Node,
keeps the unchanged native validator and executes four independent failing
browser steps. Its safe artifacts add only the owner's version/path record;
raw notebook/server payloads remain excluded.

Final scoped `43796373853` proves that installation, native validation, four
independent browser owners and portable owner Jupyter execution now reach
their intended scopes. Three browser owners and the complete owner cycle pass.
The overall diagnostic still fails: cold static initialization precedes the
plot numerics, and independent work-file receiving fails the second default
moving Python session after six stopped/one moving successes. The latter
safe receipt again retains only a generic JavaScript `Error`; its underlying
Python class/reason and native readiness are unavailable after retirement.
Add closed-vocabulary kernel-error/readiness diagnostics before further
receiving, preserving the original exception and five-second public budget.
Do not upload raw messages, secrets or arbitrary failure values, or attribute
the failure to MolSysMT before that evidence exists.

The next local helper revision retains the original Python exception privately
and carries its authored class/structured reason into the safe receipt. At
failure it passively observes frame readiness, pending query counts and
visibility; only closed names, strict booleans and bounded integers/nulls can
leave that private report. Control `970` receives 119 tests, one explicitly
unselected background profile and two deselected live cases; scoped Ruff and
Node-22 syntax checks pass. Actual live receiving remains separate. The public
five-second capture budget and every scientific assertion are unchanged.

Actual local isolated-ipykernel-7.4 receiving `971` passes the whole work-file
entry with the new helpers: six capture/restore and six strong-restore cases,
four Studio cases and all eight moving cases. Both default Python captures
keep the public five-second budget; delayed-science cases declare ten seconds.
All eight files independently recover coherent native draws and leave zero
pending saves/captures. Cancel/timeout refuse late writes. This source result
uses the retained local support composition, not the newer hosted packages;
it cannot erase the unresolved hosted default-session failure. The failing
kernel branch still needs its own actual transport control.

Review of the receiving launcher reveals that its Node selection preferred
the interpreter sibling before PATH. Consequently `971` does **not** prove
Node-22 receiving; no exact browser-child version was originally recorded.
Add explicit `--node` / `MOLSYSVIEWER_NODE` precedence, refuse a bad explicit
choice without fallback, and retain the resolved executable/version/hash in
the receipt. Default legacy selection remains available and is now identified.
This is receiving provenance work, not a production or scientific correction.

Actual transport control `973` receives a genuine failing Python execute
through the unchanged live `kernel()` helper, preserves its `ValueError` and
private sentinel in the original error, exposes only the closed class/reason,
and then executes a successful real request. The launcher explicitly records
Node 22.23.4 and its hash. This private prefix runs zero molecular/capture
cases and does not qualify the background profile used to launch it. The
601 affected Python/workflow/privacy/reporting cases in `974` pass without
failures/errors/skips; three live cases are explicitly deselected.
