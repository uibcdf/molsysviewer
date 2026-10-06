# Python ecosystem policy adoption

**Reviewed: 2026-10-06.** The support-library and developer-tool reviews remain
independent: support libraries are **adopted** and developer tools are
**adopted**, under `uibcdf/molsysviewer#110`. The shared policy
is owned by `uibcdf/molsyssuite#56`; local dependency declarations alone do not
establish adoption.

## Published support-library receiving check — 2026-10-06

**Done on Linux x86_64 / Python 3.14.8:** published SMonitor **0.19.0, build
`py_1`**, and ArgDigest **0.15.0, build `py_0`**, pass the bounded installed
MolSysViewer integration. A fresh public-channel Conda environment uses public
MolSysMT 0.22.4, DepDigest 0.13.0 and PyUnitWizard 0.28.1. No package is editable;
all inspected imports come from that environment's site-packages. Archive
SHA-256 values match the providers' release receipts, and every installed
SMonitor/ArgDigest package member matches its archive (50/47 files).

Viewer is a locally built wheel from fixed commit
`6be2bcd272ef6eda014c4bb3cf6f50f04695e8ef`, version
`0.23.4+105.g6be2bcd2.dirty`. The snapshot's generated runtime is rebuilt for
that version; all 615 library Python files other than generated `_version.py`
match the fixed source. All 620 installed package members match the wheel.
Source/wheel runtime-version validation and `pip check` pass. This wheel is
development evidence, not a public Viewer release or a frozen 1.0 candidate.

The six receiving guards in `tests/test_smonitor_application_policy.py` pass
with both the editable development providers and the exact published packages.
Cold imports in Viewer/MolSysMT/ArgDigest order, Viewer reload and rendering
for an explicit audience preserve the application's profile, level, capture
flags, enabled state and installed warning/logging handlers. Catalog registration
still supplies templates with diagnostics disabled. These guards require the
additive SMonitor 0.19.0 provider-registration API and explicitly skip older
supported versions; the receiving coordination is `uibcdf/molsyssuite#106`.
Existing installed catalog, signal, public argument validation and explicit
bypass checks pass **116 tests, 14 expected skips** (templates without
placeholders). Together with the six import guards, this is **122 passes**.

Public dependency minima remain `smonitor>=0.13.0` and `argdigest>=0.13.0`.
No new default capture policy, pipeline-only mode or explicit provider-policy
opt-in is selected. This validates the existing consumer against the released
providers; it does not qualify older bounds, other platforms, a compatible
published Interactions backend or the complete installed pair. Subsequent
qualification of Viewer 0.24.0 build 1 with MolSysMT 0.23.0 ABI3 build 0 passes
all sixteen installed staging cells and the exact Windows launchers. Canonical
source Python 3.14 integration passes on Linux, macOS and Windows, including
39 core browser suites and all 25 documented notebooks on Linux. See the
[current qualification](installed_artifact_qualification.md) and
[exact receipt](stabilization_024_preparation_20261006.json). Public-pair and
final 1.0 gates remain pending; the support-library receiving evidence below
retains its earlier candidate and scope.
Hashes, provenance, test selections and reproduction commands are retained in
[the receiving receipt](support_library_receiving_20261006.json).

The complete development-source suite runs once: **2,879 passed, 23 skipped,
two failed**, exit 1, in 507.07 s. The failures are the real offscreen Qt event
transport and payload-generation probes, which supply no readiness/report
after native OpenGL RHI initialization failures. They are recorded under
experimental `uibcdf/molsysviewer#109`; no graphical workaround or second
complete run is made. This is not a passing full suite. Commit `a48478fc`
publishes the receiving guard and installed evidence, with successful hosted
MolSysSuite policy and Conda governance checks. Its three-platform source-pair
CI now passes on Linux, macOS arm64 and Windows: 2,875/2,848/2,849 passes,
27/54/53 skips respectively. Linux also passes all 39 core browser suites and
25 documented notebooks. Run `37530734789` uses exact MolSysMT source
`a0ceca86ec99c89377e78fac15cbdf32145a362e`; this completes source evidence
without replacing the installed-package gates.

## Applicable support boundaries

| Library | Applicable boundary and existing evidence | Remaining scope |
| --- | --- | --- |
| ArgDigest | Ordinary public entrypoints digest arguments; scoped MolSysMT wrappers pass the public bypass through. `tests/test_argdigest_public_api.py`, `tests/test_public_entrypoint_contract.py` and `tests/test_support_integrations.py` protect these paths. | Quarantined unreachable digesters are a separate cleanup under `uibcdf/molsysviewer#78`; they are outside the ordinary public surface. |
| DepDigest | Hard dependencies are checked before lazy public imports; optional engine guards and loader form mappings are explicit. `tests/test_support_integrations.py` and `tests/test_dependency_contract.py` protect the applicable routes. | No blanket claim that every optional external engine has been certified. |
| SMonitor | Public diagnostic catalog templates and real rendering in five profiles are guarded by `tests/test_smonitor_integration.py`; `uibcdf/molsysviewer#107` is resolved and integrated. | Public release of the accumulated corrections remains separate from their staged qualification. |
| PyUnitWizard | Reuse the shared registry and preserve an application's active unit policy. Convert physical scene inputs explicitly to the wire unit. Scalar values retain quantities and explicit physical ranges require compatible units. `tests/test_units_under_a_user_policy.py` and `tests/test_scalar_color_units.py` protect these conversions and whole/region attributes. | Publication and exact-candidate qualification remain separate; no region scoring-threshold API is introduced. |

`uibcdf/molsysviewer#98` resolves the last reviewed support-library gap.
The normative scalar contract is in [`units_and_quantities.md`](units_and_quantities.md):
physical quantities retain their units, explicit ranges carry compatible units,
and bare numeric data remain unit-free. Automatic ranges and dimensionless
quantities remain supported. Whole/region canvas inputs use the same boundary.

## Developer tools

Published Pytest Receptor **1.2.0** is pinned in the main-test, Python 3.14
source-pair and development Conda environments, and the development extra.
PyPI's wheel SHA-256 is
`4e339abd53d85406c3acc0c643b895154b133c0a6f9d5f7a2350703f514a9971`;
the uibcdf channel publishes `noarch/pytest-receptor-1.2.0-py_0.tar.bz2`.
Both distributions declare Python >=3.11,<3.15. The isolated local validation
imports the published wheel, rather than the editable provider checkout.

Use `llm` locally and `ci` for the maintained hosted pytest commands. Preserve
native exit codes, full-suite selection, Qt selectors, coverage XML and JUnit
XML. Configure executable rerun commands for the interpreter used to run tests.
`tests/test_python_ecosystem_contract.py` guards these configuration boundaries;
[`pytest_receptor.md`](pytest_receptor.md) records the invocation contract.

Published GH Run Receptor **1.1.1**, with the eight valid workflow rules in
`.github/gh-run-receptor.yaml`, was used for first inspection of the exact CI,
core E2E, policy, nightly and probe runs recorded in the resolution of
`uibcdf/molsysviewer#116`. It was also used to inspect the failing PR #135 runs.
Native GitHub records settle executed steps and primary errors when compact
output is incomplete. A compact verdict does not approve a release.

## Source and hosted qualification

[PR #135](https://github.com/uibcdf/molsysviewer/pull/135) isolates the developer-tool
changes at `4ef65a8e5403ace672e571bd0123aab7becfae71` from the larger unpublished
working tree. Five new configuration checks pass with both `llm` and `ci`.
The corrected source dependency/distribution/configuration checks pass (52 tests),
and the scoped branch checks pass (23 tests). Ruff passes on the scoped branch.

One complete local run with the published receptor returned exit 1: 2,441 passed,
23 skipped, 26 failed. Four configuration regressions were corrected and their
affected tests pass. The remaining sandbox socket and Chromium/Qt restrictions
were confirmed from native diagnostics; their focused rerun outside the sandbox
passes 55 tests, with one expected skip. The full suite was not repeated, in
accordance with the repository's one-full-run rule. This is not a new full-suite
pass or qualification of a 1.0 artifact.

The first PR runs at `c95a231db4fac86415c2eab1793a0a75384ded55` failed before
pytest: [CI 36882496875](https://github.com/uibcdf/molsysviewer/actions/runs/36882496875),
[E2E 36882496876](https://github.com/uibcdf/molsysviewer/actions/runs/36882496876),
and [source pair 36882496937](https://github.com/uibcdf/molsysviewer/actions/runs/36882496937).
Native logs show Conda download timeouts for channel indexes and packages;
subsequent activation/cleanup errors do not identify the primary failure.
The PR aggregate correctly fails when its constituent jobs fail. The first
policy run exposed an existing import-format error; its bounded correction is
included in the second commit.

The corrected commit `4ef65a8e5403ace672e571bd0123aab7becfae71` passes
[CI 36885559251](https://github.com/uibcdf/molsysviewer/actions/runs/36885559251),
[core E2E 36885559507](https://github.com/uibcdf/molsysviewer/actions/runs/36885559507),
[Python 3.14 source pair 36885559580](https://github.com/uibcdf/molsysviewer/actions/runs/36885559580),
[policy 36885559907](https://github.com/uibcdf/molsysviewer/actions/runs/36885559907),
[Ruff 36885559216](https://github.com/uibcdf/molsysviewer/actions/runs/36885559216),
and [Conda governance 36885559780](https://github.com/uibcdf/molsysviewer/actions/runs/36885559780).
Native job records confirm six executed Python 3.11–3.13 cells, both Qt steps,
the Ubuntu 3.13 JS step, the successful PR aggregate, executed core E2E, and
three executed Python 3.14 source-pair cells. Every pytest job passed its
installed Pytest Receptor 1.2.0 version assertion. GH Run Receptor 1.1.1 was
used for first inspection; native records settle the final executed steps.

Developer-tool adoption is therefore **adopted** for this reviewed implementation.
PR #135 is merged; the original and updated-commit evidence is recorded here.
These results qualify the
scoped branch's test-tool integration, not the larger unpublished product work
or a future 1.0 artifact.

## Final support-library qualification — 2026-10-01

The #98 correction passes 21 dedicated tests, including physical equivalent
units, non-default policy, real native attributes, canvas handlers and replay.
The final focused run including the public ArgDigest module passes 24 tests;
76 existing color/unit checks also pass. The single complete source run outside
the sandbox returned exit 1: 2,480 passed, 23 skipped and one failed. An existing
B-factor fixture supplied bare bounds; it now supplies explicit physical units,
and its module passes in the focused rerun. The complete suite was not repeated.
This evidence closes the reviewed boundary without claiming a new full-suite pass.

The runtime rebuild passes. Native Node outside the sandbox executes 296 JS
tests successfully, including the three range-input guards. The sandbox's
isolated file-level report is excluded from the test-count evidence.
Support libraries and developer tools are therefore **adopted** for their
reviewed boundaries, closing `uibcdf/molsysviewer#110`. The larger working tree
remains unpublished apart from the scoped tooling changes merged in PR #135.
Installed artifacts, scientific
workflows and the final release candidate retain their independent gates.

## Integration and publication — 2026-10-01

PR #135 was updated with current `main` to
`84cbc6bf6475236d3afd53c901b0ca47bb2b99d1`. All checks pass, including
[CI 36907639608](https://github.com/uibcdf/molsysviewer/actions/runs/36907639608),
[core E2E 36907639873](https://github.com/uibcdf/molsysviewer/actions/runs/36907639873)
and [source pair 36907639590](https://github.com/uibcdf/molsysviewer/actions/runs/36907639590).
It merged at `12faa16b76872fa495a664d8a9ce78ee6fd5438e` without bypassing
the required checks. Local integration preserves the accumulated work and both
local promotion preconditions and the upstream shared installed-matrix action;
186 focused release/reporting/configuration tests pass. The remaining scientific
and design changes are still in the working tree. The principal maintainer
authorizes continued commits and direct pushes, with PRs only on request.
