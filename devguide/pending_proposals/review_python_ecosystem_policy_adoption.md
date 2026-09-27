---
summary: Review MolSysViewer Python ecosystem policy adoption.
issue: uibcdf/molsysviewer#110
status: active
opened: 2026-09-27
closed:
verification: inspected
area: [governance, tooling]
guard:
normative:
blocked_by: []
supersedes: []
---

# Review Python ecosystem policy adoption

**Proposal state: proposed.**

**Reported:** 2026-09-27, during the six-member inventory coordinated by
`uibcdf/molsyssuite#56`. The source inspected was
`19dadc1a0adb1ff7477fe9e7866e807b015c8f36` on `origin/main`.

## What

MolSysViewer's support-library and developer-tool reviews in the suite registry
were both `pending`. This report records their applicable boundaries, the evidence
already present, and the remaining work. The two policies need independent states.

## How

The support-library review is **partial**. `pyproject.toml` declares ArgDigest,
DepDigest, SMonitor, and PyUnitWizard as runtime dependencies. Public viewer and
configuration methods use ArgDigest digestion and SMonitor signals; loader paths
use DepDigest; configuration, camera, quantity, and unit-policy paths use
PyUnitWizard. `tests/test_support_integrations.py`,
`tests/test_units_under_a_user_policy.py`, and
`tests/test_smonitor_integration.py` exercise representative integration
boundaries. The emitted SMonitor catalog still has six codes without renderable
templates (`uibcdf/molsysviewer#107`). That defect blocks a complete diagnostics
claim. Continue the public-boundary review with the unit contract tracked in
`uibcdf/molsysviewer#98`; the quarantined, unreachable digesters are tracked
separately in `uibcdf/molsysviewer#78`.

The developer-tool review is **partial**. Root `AGENTS.md` and
`devguide/pytest_receptor.md` document `--receptor=llm` for agent runs, and the
Python 3.14 source-pair workflow invokes `--receptor=ci`. However,
`devtools/conda-envs/test_source_pair_py314.yaml` names `pytest-receptor`
without an exact published version. The main `devtools/conda-envs/test_env.yaml`
does not install it, and the maintained `CI.yaml` pytest commands do not select
the `ci` profile. `.github/gh-run-receptor.yaml` has workflow profiles, but this
review has not yet established an exact published tool version and observed
first-inspection route for Actions runs.

Next, pin a reviewed published Pytest Receptor release in each applicable hosted
test environment, select `--receptor=ci` for its pytest commands without
changing test selection or verdicts, and verify exact-commit hosted results.
Record the GH Run Receptor version and run-inspection evidence separately.
Resolve or bound the support-library gaps before claiming either policy as
adopted. Keep implementation and test changes in this repository; update the
suite inventory from measured results.

## Why

A dependency declaration, a configured workflow profile, or one Python 3.14
source-pair lane does not establish adoption across MolSysViewer's maintained
public boundaries and CI routes. Separate partial states keep existing
integration evidence visible without treating open gaps as complete.

## What was refuted

No installed-package or hosted test run was performed in this review. Source
inspection refutes the shortcut of treating four declared dependencies as a
complete support-library review, because `uibcdf/molsysviewer#107` identifies
an unresolved diagnostic path. It also refutes treating the source-pair
`--receptor=ci` commands as complete developer-tool adoption, because the main
test matrix still runs plain pytest and the source-pair tool pin is not exact.

## Resolution

Open. Reassess each policy after the applicable member changes and exact-commit
evidence are recorded. Link the eventual regression checks and the final suite
inventory state when closing this issue.
