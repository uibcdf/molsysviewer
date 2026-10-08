---
summary: Public setup commands must use the published Conda route.
issue: uibcdf/molsysviewer#95
status: resolved
opened: 2026-09-24
closed: 2026-10-07
verification: inspected
area: [documentation, packaging]
guard: tests/test_public_installation_contract.py::test_public_installation_commands_use_published_conda_channel
normative: devguide/public_distribution_contract.md
blocked_by: []
supersedes: []
severity: medium
---

# Public setup commands must use the published Conda route.

**Recorded:** 2026-10-07 while reconciling the existing issue; this date records the local report, not the original issue opening.

## What / how / why

README offered `pip install molsysviewer`, although no supported public PyPI route supplies MolSysViewer and its required UIBCDF backend. Troubleshooting repeated that route for upgrades. Source-install recipes do not establish a public PyPI distribution.

## Resolution

Use the public Conda channels in README, installation and troubleshooting. State explicitly that MolSysMT is the required core backend; remove the obsolete claim that a ten-panel MolSysMT addon is required/discovered on install. Update the repaired Windows launcher statement and use the provisioned development environment with `build:runtime`.

The guard extracts actual setup commands from Markdown and notebook narrative, rejects public pip package installs and requires the UIBCDF channel on Conda package commands. Editable local source setup is a separate developer route. No dependency or package artifact changes.
