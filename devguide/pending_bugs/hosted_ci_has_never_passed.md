---
summary: Hosted CI has never passed, for three causes that live in how CI builds its environment.
issue: uibcdf/molsysviewer#88
status: open
opened: 2026-09-19
closed:
severity: high
verification: measured
area: [ci, packaging, testing]
guard:
normative:
blocked_by: []
supersedes: []
---

# Hosted CI has never passed

The local suite was green on every commit where hosted CI was red, so the local suite
could not have shown this. All three causes are in how CI builds its environment, which
the local environment never exercises: the siblings are editable installs from `../`,
and `_version.py` already exists.

## What was measured

On 2026-09-19, with `gh run list --workflow <name> --limit 200`:

| Workflow | Runs returned | Successes | Last success |
| --- | ---: | ---: | --- |
| `CI` | 200 | 0 | none in the window |
| `Documentation notebooks` | 29 | 0 | never |
| `CI_e2e` | 200 | 69 | 2026-07-14, `5d826e16` (run 29359069988) |

`Ruff Lint` and `MolSysSuite policy` pass. The 2026-09-06 closing state (`af97098d`)
was reported as green, but that was a local result. CI, CI_e2e and Documentation
notebooks all failed on that commit and on every commit around it.

## Cause 1: the MolSysMT this package declares does not exist

`pyproject.toml` requires `molsysmt>=0.22.0`, a requirement added in `66a5bd02`
(2026-08-14). What exists:

- MolSysMT's newest tag is `0.21.0`, and its `main` is 635 commits past it
  (`git -C ../molsysmt describe --tags` → `0.21.0-635-ga68454a24`).
- The newest MolSysMT on the `uibcdf` channel is `0.12.0` (`mamba search -c uibcdf
  --override-channels molsysmt`), and its newest GitHub Release is also `0.12.0`, from
  2025-12-07. The channel has no Python 3.13 build of it.

Effects, from run 34890243748 (`96f12779`):

- **Python 3.13 test jobs, the Qt pipeline job and `Documentation notebooks`:** the
  solver fails before any test runs:
  `molsysmt [0.11.2|0.11.3|0.12.0] would require python_abi =3.10|3.11|3.12 …
  python =3.13 * is not installable`. `docs_env.yaml` pins `python=3.13`, so the
  notebooks workflow can never solve.
- **Python 3.11 and 3.12 jobs:** the environment solves, with MolSysMT `0.12.0`. The
  package is then installed with `pip install . --no-deps`, so the unsatisfiable
  `>=0.22.0` is never checked. These jobs failed on cause 2. Without it they would have
  tested this package against a MolSysMT nine months older than the one it is written
  against, and a green result there would have meant nothing.

This is Phase 10 gate 1 as seen from CI, and this repository cannot close it: it needs
a MolSysMT release on the channel with Python 3.11–3.13 builds. The other siblings on
the channel (`argdigest` 0.12.1, `depdigest` 0.10.1, `smonitor` 0.15.0, `pyunitwizard`
0.25.0) match their latest tags. Their latest builds are listed as `py311`; whether
those are `noarch` has **not been checked**.

## Cause 2: `test_env.yaml` lacks `aiohttp`

`aiohttp>=3.10` is a declared runtime dependency, and `devtools/conda-envs/test_env.yaml`
does not list it. Because the package is installed with `--no-deps`, nothing brings it
in. In the same run, on Python 3.12, four modules fail at collection with
`ModuleNotFoundError: No module named 'aiohttp'`: `test_internal_render_worker_host.py`,
`test_remote_cli.py`, `test_remote_digesters.py` and `test_remote_protocol.py`.

**The general form of the defect** is that the environment file restates
`pyproject.toml` by hand, and the two drifted. Adding the one missing name repairs this
occurrence. A guard comparing the two lists is what would keep it repaired.

## Cause 3: `CI_e2e` never generates `_version.py`

`.github/workflows/CI_e2e.yaml` sets up Node, then runs `npm ci` and `npm run build`.
`build` is `sync:pyversion && build:runtime`, and both read `molsysviewer/_version.py`.
That file is git-ignored and written by versioningit only when the Python package is
built or installed, and this workflow installs no Python. Every sampled failure since
2026-08-08 stops there, the latest being run 35468886760 (`72562f44`):

```
Error: ENOENT: no such file or directory, open '…/molsysviewer/_version.py'
```

Before that, on 2026-07-31 (run 30619723193), the job was getting further and failing on
`ModuleNotFoundError: No module named 'depdigest'`. So some E2E scenarios need a Python
environment with the package installed. Examples are the bridges such as
`tests/e2e/exported-page-colour-bridge.py`. Repairing the build step will therefore
expose those scenarios to cause 1. They are fixable here only as far as the build.

## What this invalidates

- **Phase 10 gate 8** is recorded in
  [`../pre_1_0_architecture_rework_and_hardening_master_plan.md`](../pre_1_0_architecture_rework_and_hardening_master_plan.md)
  as *Done: notebook execution is enforced by `.github/workflows/docs-notebooks.yaml`*.
  That workflow has not passed once. What exists is a workflow, not enforcement, so the
  gate is open until it passes.
- Any report that called the project green on the basis of a local run alone. From here
  on, "green" means the hosted workflows as well, or it says which workflows it covers.

## A related local fragility (not a CI cause)

`tests/test_release_gate.py::test_the_version_check_enforces_the_runtime_and_only_reports_the_manifest`
runs `_check_version_consistency()` from `devtools/release_gate.py` on a development
checkout. The check requires the string in `_version.py` to appear in the committed
`viewer.js`. That is a correct release invariant, but on a development checkout it is
false whenever the package has been reinstalled after a commit:

- On 2026-09-06 at 13:18, after `af97098d`, an editable reinstall rewrote `_version.py`
  to `0.23.0+17.g3fa27e68`. `viewer.js`, built at 08:39 that day, carries `0.23.0`.
- On 2026-09-19 that is the one failure in the local suite.

Rebuilding the runtime would make the test pass by writing a development version string
into a tracked file, which is worse. Where this invariant is checked is a decision still
to be taken. The release gate itself is the natural place. The unit test could instead
check that the comparison works, rather than that this particular checkout happens to
satisfy it.

## Recommended corrections

1. **Cause 2:** add `aiohttp>=3.10` to `test_env.yaml`, plus a test that every
   `pyproject.toml` runtime dependency appears in `test_env.yaml`. Mutation-verify it by
   removing one name.
2. **Cause 3:** have `CI_e2e` produce `_version.py` before `npm run build`, by
   installing the package with its Python environment. The Python-backed scenarios will
   then meet cause 1, and the report should say so rather than skip them.
3. **Gate 8:** set its status in the master plan to what is actually enforced, pointing
   here.
4. **Cause 1:** closes with Phase 10 gate 1, once MolSysMT is released on the channel
   with 3.11–3.13 builds.
5. **The version test:** a decision, recorded here when taken.

## Acceptance

- `CI`, `CI_e2e` and `Documentation notebooks` pass on `main` against the MolSysMT this
  package declares, not an older one the solver happens to find.
- Gate 8 says what is enforced.
- Causes 2 and 3 may close before cause 1. This entry closes with cause 1, and it may
  pass through `partial` on the way.
