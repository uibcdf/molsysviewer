---
summary: The fifth hosted pytest command is absent from the workflow rerun inventory.
issue: uibcdf/molsysviewer#399
status: resolved
opened: 2026-11-16
closed: 2026-11-16
severity: medium
verification: reproduced
area: [ci, diagnostics, pytest]
guard: tests/test_python_ecosystem_contract.py
normative:
blocked_by: []
supersedes: []
---

# Covering workflow pytest contract

**Resolved in source after covering-workflow correction.** The previous
[preparation and diagnostic correction](focused_source_diagnostic_preparation.md)
remains received within its stated scope. Covering source checkpoint
`43816742412`, MolSysViewer `b84615763867b6f3833c54a516615599503af51f`
and MolSysMT `4b0b1f8a17e010e5ea9f28a8032a1bb06a1daa69`, fails the same
whole-workflow test on all three Python 3.14 hosts. Linux reports 4,738 passes,
42 skips, 17 deselections and one failure; Windows reports 4,711 passes,
69 skips and the same failure; macOS reports 4,707 passes, 73 skips and the
same failure. Those are independent host outcomes, not combined qualification.

`test_every_hosted_pytest_command_selects_ci_and_an_executable_rerun`
still expects four commands in `ci-python-314-source-pair.yaml`. The added
explicit owner cycle makes five. Inspection also identifies a second part
of the same integration omission: that fifth command has no explicit
`-o "receptor_rerun_command=python -m pytest"`. Merely updating the inventory
would expose its missing option. Keep the existing assertions on every
command; add the required override to the actual owner invocation and update
the reviewed count. This changes no scientific selection or product deadline.

Both corrections are now applied. All seven cases in the actual affected
module pass in bounded source run `988`; the original per-command checks
remain intact. A separate retained private control invokes the real guard
on three source/YAML variants: the original rejects the command count, the
inventory-only variant rejects the missing rerun option, and both corrections
pass all three workflow contracts. An initial diagnostic helper's overly
specific Python exception-message assertion is retained separately; it is
neither a product failure nor a passing full control.

The previous 600-case local selection did not include this whole-workflow
module. Final `990` now passes all 518 selected workflow, protocol, archive
and reference checks, including those seven affected cases. `989`'s initial
record check correctly rejects the new archive link before its target is
staged for a clean checkout; its original failure is retained and the guard
is unchanged. All three original failed jobs and their hash-verified JUnit
artifacts remain preserved. Their browser and notebook gates were not reached, and their
passing Python cases do not make the runs successful. The two-line correction
was applied only after #354's frozen thirty-cycle campaign completed and its
owned processes retired. Candidate, installed, human and
publication acceptance remain separate.
