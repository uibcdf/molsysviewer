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
