# Public distribution and host scope

**Reviewed: 2026-10-07.** Conda is the public MolSysViewer installation route,
using `uibcdf`, `conda-forge` and `ambermd`. There is no public PyPI installation
promise. A developer may install a source checkout into a provisioned suite
environment; that is not a separate public package channel.

The immutable Viewer 0.24.0 noarch build 1 / MolSysMT 0.23.0 ABI3 build 0 pair
passes sixteen public installed cells: Linux x86_64/ARM64, macOS Apple Silicon
and Windows x86_64, each on Python 3.11–3.14. These are recorded scientific and
installation results, not a substitute for the separate central Python admission
in `uibcdf/molsyssuite#29` / `uibcdf/molsysviewer#93`. The central registry still
records Viewer as authorized on this review date; admission is pending.
Intel-based macOS is excluded from the current matrix.

The core Python/widget and interactive HTML routes are separate from native
hosts. Local standalone launchers and Qt are experimental for 1.0. A noarch
package, a successful Qt solve or an installed command's `--help` does not
certify native rendering. The detailed development recipe retains Linux
transport observations and Windows/macOS solver-only evidence in
[standalone_supported_environment.md](standalone_supported_environment.md).
Remote sessions are an unsupported preview; supported workflows remain post-1.0.

MolSysMT is the required core backend. Users do not enable a MolSysMT addon to
load, select or calculate interactions. Known legacy addon module names may
remain available for explicit discovery; their inventory is not a claim that a
current provider distributes a qualified optional workspace.

Maintain this distinction in the README, installation notebook, troubleshooting
and standalone developer page. `tests/test_public_installation_contract.py`
rejects a public pip route and unqualified native-host claims. The installed
pair and launcher evidence remains in
[installed_artifact_qualification.md](installed_artifact_qualification.md).
