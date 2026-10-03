---
summary: Review MolSysViewer Python ecosystem policy adoption.
issue: uibcdf/molsysviewer#110
status: resolved
opened: 2026-09-27
closed: 2026-10-01
verification: measured
area: [governance, tooling]
guard: tests/test_python_ecosystem_contract.py
normative: devguide/python_ecosystem_policy_adoption.md
blocked_by: []
supersedes: []
---

# Review Python ecosystem policy adoption

**Proposal state: resolved.**

**Reported:** 2026-09-27, during the six-member inventory coordinated by
`uibcdf/molsyssuite#56`. The source inspected was
`19dadc1a0adb1ff7477fe9e7866e807b015c8f36` on `origin/main`.

## What

MolSysViewer's support-library and developer-tool reviews in the suite registry
were both `pending`. This report records their applicable boundaries, the evidence
already present, and the remaining work. The two policies need independent states.

## How

The support-library review is **adopted**. `pyproject.toml` declares ArgDigest,
DepDigest, SMonitor, and PyUnitWizard as runtime dependencies. Public viewer and
configuration methods use ArgDigest digestion and SMonitor signals; loader paths
use DepDigest; configuration, camera, quantity, and unit-policy paths use
PyUnitWizard. `tests/test_support_integrations.py`,
`tests/test_units_under_a_user_policy.py`, and
`tests/test_smonitor_integration.py` exercise representative integration
boundaries. The six missing SMonitor templates identified by
`uibcdf/molsysviewer#107` have been implemented; the full-catalog guard and real
emission in all five profiles pass, as does the official SMonitor integration
verifier. The last reviewed boundary, `uibcdf/molsysviewer#98`, now retains
physical quantities through whole/region scalar coloring and requires compatible
units on explicit physical ranges. Bare data remain unit-free; automatic ranges
and dimensionless quantities are supported. Its dedicated 21-test guard includes
non-default policy, actual canvas handlers and scene/history replay. The
quarantined, unreachable digesters remain separate under `uibcdf/molsysviewer#78`.

The developer-tool review is **adopted** for the reviewed implementation.
Pytest Receptor 1.2.0 is verified as published on PyPI and the uibcdf Conda
channel and pinned in the three applicable environments and development extra.
All maintained Python CI commands select `ci`, retain selection/coverage/JUnit,
and record the installed version. Five new configuration guards pass with the
published wheel; 52 affected checks pass after correcting source-audit ordering
and preserving the existing source-pair selector. The 55 socket/browser/Qt
focused checks pass outside the sandbox (one expected skip).

The single complete local run returned exit 1 (2,441 passed, 23 skipped,
26 failed). Four configuration regressions were corrected; the other failures
were sandbox restrictions, confirmed in native diagnostics and the focused
rerun. No second complete suite was run and no new complete pass is claimed.

Published GH Run Receptor 1.1.1 and the eight valid workflow profiles were used
for first inspection of the successful implementation/nightly/probe runs closing
`uibcdf/molsysviewer#116` and of PR #135. Native GitHub records confirmed executed
steps, protection settings and the actual Conda timeout causes.

[PR #135](https://github.com/uibcdf/molsysviewer/pull/135), corrected commit
`4ef65a8e5403ace672e571bd0123aab7becfae71`, isolates the CI change from the larger
unpublished source work. Initial hosted CI/E2E/source-pair runs failed while
creating Conda environments, before pytest; those results did not qualify the
tool pin. The corrected exact commit now passes CI `36885559251`, core E2E
`36885559507`, source pair `36885559580`, policy `36885559907`, Ruff
`36885559216` and Conda governance `36885559780`. Native records confirm all
six Python matrix cells, both Qt steps, JS, the PR aggregate, core E2E, and
all three Python 3.14 source-pair cells executed successfully; every pytest
job passed its installed 1.2.0 assertion. The draft PR is ready for review and
remains unmerged.
The durable review and evidence boundaries are in
[`python_ecosystem_policy_adoption.md`](../python_ecosystem_policy_adoption.md).

## Why

A dependency declaration, a configured workflow profile, or one Python 3.14
source-pair lane does not establish adoption across MolSysViewer's maintained
public boundaries and CI routes. Separate partial states keep existing
integration evidence visible without treating open gaps as complete.

## What was refuted

No installed-package or hosted test run was performed in the original review.
The original source inspection refuted the shortcut of treating four declared
dependencies as a complete support-library review: `uibcdf/molsysviewer#107`
identified six missing templates. The 2026-10-01 local rendering checks address
that defect; the later #98 guard resolves the remaining unit boundary. The review also
refutes treating the source-pair
`--receptor=ci` commands as complete developer-tool adoption, because the original main
test matrix ran plain pytest and the original source-pair tool pin was not exact.
The correction is implemented; its hosted qualification remains separate.

## Resolution

Resolved. Developer-tool adoption is verified at the exact PR #135 commit
recorded above; support-library adoption closes with the #98 unit correction.
`tests/test_python_ecosystem_contract.py` guards published tool pins, profiles
and maintained test commands; `tests/test_scalar_color_units.py` guards the final
support boundary. `devguide/python_ecosystem_policy_adoption.md` absorbs the
applicable rules and qualification limits. The suite registry records both
reviews as `adopted`.

The #98 final focused run passes 24 tests (21 dedicated and three public
ArgDigest checks); 76 existing color/unit checks passed. The single complete
source run for that implementation returned 2,480 passed, 23 skipped and one
failed because an existing B-factor fixture supplied bare bounds. Its input
now carries physical units and the module passes in the focused rerun. No
second complete run or new full-suite pass is claimed. The runtime rebuild and
all 296 native JS tests pass outside the sandbox. These observations qualify
the reviewed boundaries; publication of the working tree, merge of draft PR
#135 and exact-candidate release qualification remain separate.

## Publication addendum — 2026-10-01

After the closure above, the principal maintainer authorized merging PR #135
and continuing ordinary work with commits and direct pushes. The PR was updated
to `84cbc6bf6475236d3afd53c901b0ca47bb2b99d1`; CI `36907639608`, core
E2E `36907639873`, all three source-pair cells in `36907639590`, Ruff and
the policy/publication checks pass. The merge reached `main` at
`12faa16b76872fa495a664d8a9ce78ee6fd5438e` without bypassing required checks.
The local checkout advanced to that commit with all accumulated work preserved.
The source integration retains both the local promotion preconditions and the
upstream shared installed-matrix checks; 186 focused integration tests pass.
The scoped tooling changes are now published. The other product changes and
the final 1.0 qualification remain separate. Root `AGENTS.md` records the
accepted direct development workflow; this addendum preserves the original
unmerged status as evidence of the state at closure.
