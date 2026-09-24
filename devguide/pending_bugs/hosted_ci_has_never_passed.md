---
summary: Hosted CI has never passed, for three causes that live in how CI builds its environment.
issue: uibcdf/molsysviewer#88
status: partial
opened: 2026-09-19
closed:
severity: high
verification: measured
area: [ci, packaging, testing]
guard: tests/test_distribution_artifact.py::test_every_environment_installed_without_deps_carries_the_runtime_dependencies, tests/test_js_build_version_resolution.py, tests/test_release_gate.py
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

This is Phase 10 gate 1 as seen from CI. The public path needs a MolSysMT release on the
channel with Python 3.11–3.13 support; the coordinated pair can and must be proved first
on the staging label.

The hygiene question about the supporting packages was checked on 2026-09-19. The
inspected Linux records for `argdigest` 0.12.1, `depdigest` 0.10.0 and `smonitor` 0.13.0
are **not noarch**: their `py311_1` files live under `linux-64` and constrain both
`python>=3.11,<3.12.0a0` and `python_abi=3.11`. Separate `py312` and `py313` records are
present on that platform. This does not explain the current Python 3.13 failure; the
solver tree names the absence of a compatible public MolSysViewer package.

## Cause 2: `test_env.yaml` lacks `aiohttp`

`aiohttp>=3.10` is a declared runtime dependency, and `devtools/conda-envs/test_env.yaml`
does not list it. Because the package is installed with `--no-deps`, nothing brings it
in. In the same run, on Python 3.12, four modules fail at collection with
`ModuleNotFoundError: No module named 'aiohttp'`: `test_internal_render_worker_host.py`,
`test_remote_cli.py`, `test_remote_digesters.py` and `test_remote_protocol.py`.

**The general form of the defect** is that the environment file restates
`pyproject.toml` by hand, and the two drifted. Adding the one missing name repairs this
occurrence. A guard comparing the two lists is what would keep it repaired.

**Fixed on 2026-09-19.** Both `test_env.yaml` and `docs_env.yaml` now carry every runtime
dependency with the floor `pyproject.toml` declares, and
`test_every_environment_installed_without_deps_carries_the_runtime_dependencies` derives
the environments to check from the workflows that install the package with `--no-deps`,
so one added later is checked without anyone remembering. Mutation-verified four ways:
dropping `depdigest`, and weakening the `aiohttp`, `molsysmt` and `smonitor` floors, each
fails naming exactly what is missing.

Carrying `molsysmt>=0.22.0` changes what CI does on 3.11 and 3.12: instead of resolving
0.12.0 and testing against it, the solver now fails naming the release that does not
exist. That is the intended outcome. Red for a reason that is true beats green for a
reason that is not.

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
environment with the package installed: 13 of the 37 drive the page from a bridge such as
`tests/e2e/exported-page-colour-bridge.py`, and `molsysviewer` imports `molsysmt` at
module level. Repairing the build therefore exposes those scenarios to cause 1.

**Fixed on 2026-09-19.** `CI_e2e` now creates the `test_env` environment and installs the
package before the npm steps, which is what writes `_version.py` — measured in a clean
clone: `pip install . --no-deps` leaves the file in the source tree. The npm steps run in
a login shell so the bridges get that environment's interpreter, and its `nodejs` serves
npm, as it already does for the JS step in `CI.yaml`.

### The same defect had stopped three npm releases and would have stopped conda

`build-runtime.mjs` read `_version.py` directly, while `sync-python-version.mjs` — the
other half of the same `npm run build` — already fell back to `RELEASE_VERSION`,
`GITHUB_REF_NAME` or `GIT_REF_NAME`. `f4afc675` (2026-08-05) introduced that read, and the
divergence is exactly as old:

- **npm.** `@uibcdf/molsysviewer` carries `0.0.2, 0.5.3, 0.6.0, 0.6.1, 0.7.0, 0.20.0`, and
  `0.20.0` was published on 2026-08-05 at 10:43, seven hours before that commit. The three
  tags since — `0.20.1`, `0.22.0`, `0.23.0` — each ran `NPM Release` and each failed with
  the same `ENOENT`. So every `shared_runtime="cdn"` export produced by those versions
  points at a runtime npm does not have. This is the failure the workflow's own header
  says it was written to end, returning in a different place. Tracked as
  uibcdf/molsysviewer#89.
- **conda.** `devtools/conda-build/build.sh` exports `RELEASE_VERSION` from `PKG_VERSION`
  precisely so the bundle can be built before `pip install`, and it builds in that order.
  Nothing has published a conda package since 2025-12-28, so this never showed as a
  failure; the next release would have hit it. Phase 10 gate 2 would have opened onto it.

**Fixed on 2026-09-19.** Both scripts resolve through a new
`molsysviewer/js/scripts/resolve-version.mjs`: `_version.py` first, then the release
environment, then the manifest, and the last two say so out loud.
`tests/test_js_build_version_resolution.py` builds the runtime from a miniature source
tree with no `_version.py` and a `RELEASE_VERSION` in hand, asserts the file outranks the
environment, checks the manifest resolves the same way, and refuses any build script that
parses `_version.py` on its own. Mutation-verified: restoring the old `build-runtime.mjs`
fails two of them; removing `RELEASE_VERSION` from the resolver fails two.

## What this invalidates

- **Phase 10 gate 8** is recorded in
  [`../pre_1_0_architecture_rework_and_hardening_master_plan.md`](../pre_1_0_architecture_rework_and_hardening_master_plan.md)
  as *Done: notebook execution is enforced by `.github/workflows/docs-notebooks.yaml`*.
  That workflow has not passed once. What exists is a workflow, not enforcement, so the
  gate is open until it passes.
- Any report that called the project green on the basis of a local run alone. From here
  on, "green" means the hosted workflows as well, or it says which workflows it covers.

## A related local fragility (not a CI cause)

`test_the_version_check_enforces_the_runtime_and_only_reports_the_manifest`, as it stood
until this entry, ran `_check_version_consistency()` from `devtools/release_gate.py` on
the development checkout it happened to be in. The check requires the string in
`_version.py` to appear in the committed `viewer.js`. That is a correct release invariant,
but on a development checkout it is false whenever the package has been reinstalled after
a commit:

- On 2026-09-06 at 13:18, after `af97098d`, an editable reinstall rewrote `_version.py`
  to `0.23.0+17.g3fa27e68`. `viewer.js`, built at 08:39 that day, carries `0.23.0`.
- On 2026-09-19 that is the one failure in the local suite.

Rebuilding the runtime would make the test pass by writing a development version string
into a tracked file, which is worse.

**Decided and done on 2026-09-19:** the check now takes the reported version, the runtime
and the manifest as arguments. The suite exercises the comparison on versions it chooses —
a runtime built from another version is refused, a matching one is accepted, a lagging
manifest is reported rather than enforced, and an absent runtime fails — while the
statement about *this* checkout stays in `devtools/release_gate.py`, which still answers
`RELEASE BLOCKED — failing: version` here, because that is where the question is being
asked. Mutation-verified: neutering the comparison or tolerating an absent runtime each
fails a test.

The general lesson is worth more than the fix. The old test was not wrong about the
invariant; it asserted it in a place where it is routinely and legitimately false. A guard
in the wrong place is indistinguishable from a broken guard, and it trains people to
ignore a red suite — which is what happened here, on a repository whose CI was already
red.

## One measurement that nearly became a false finding

While verifying the above, the `remote-client-rendering` E2E scenario failed twice with
`Timeout 30000ms exceeded while waiting for event "download"` on the PNG export. Reverting
the 302 Python files that `918cd35a` ("style(ruff): normalize Python sources") had touched
made it pass; reverting only `molsysviewer/remote/` also made it pass. Two observations,
one clean story: a formatting commit had changed behaviour.

It was wrong. Comparing the ASTs of every one of those 302 files against their previous
versions, with string whitespace normalised, showed 118 files with real differences and
**none of them under `molsysviewer/remote/`** — the seven remote files are semantically
identical. The scenario then passed three times in a row on the untouched tree.

What actually distinguishes the runs is load: both failures happened while the full Python
suite was running on the same machine, and all five passes happened with the machine free.
A 30-second wait for a browser download is not generous enough to survive a busy host.
Worth knowing before the same scenario is run on a CI runner, which is a smaller machine
than this one.

## Coordinated staging path — implemented, execution pending

MolSysMT has already completed the one bootstrap step that cannot test itself. Workflow
run `33849332945`, exact commit `e5820d4794f8ce31a1f64e345c5edf9073ade975`, published
MolSysMT 0.22.0 build-2 ABI3 artefacts to `uibcdf/label/staging` for all five native
platforms. Live channel queries on 2026-09-19 found one build on each of `linux-64`,
`linux-aarch64`, `osx-64`, `osx-arm64` and `win-64`.

That is necessary but not sufficient. A Linux dry-run using staging and requesting
`python=3.13 molsysmt=0.22.0` still fails because MolSysMT depends on MolSysViewer and the
public MolSysViewer records stop before Python 3.13. The same request resolves for Python
3.12. The result identifies the dependency cycle; it does not justify promoting MolSysMT
untested.

MolSysViewer now has the missing second half:

- the manual Conda workflow requires an exact candidate SHA and version, validates their
  identity, builds against the staging channel, executes the recipe tests and uploads
  only to the staging label;
- a GitHub Release remains the only path to the public label and uses a distinct build
  number, so verified staging bytes are never overwritten under the same coordinate;
- `CI`, `CI_e2e` and `Documentation notebooks` expose an explicit manual
  `use_staging` input which pins MolSysMT 0.22.0 and puts staging first; their ordinary
  triggers continue using only the public channel;
- guards reject a staging path that skips the recipe test, loses exact-SHA checkout,
  merges the staging and release labels, drops producer evidence or leaves any hosted
  gate unable to select the candidate.

This is source readiness, not release evidence. It becomes evidence only after a new
MolSysViewer candidate is frozen, uploaded and the hosted gates plus MolSysMT's
five-platform × three-interpreter exact-pair matrix pass. The existing `0.22.0` and
`0.23.0` tags predate the #88/#89 packaging fixes and must not be moved; a new patch
candidate is required.

Suite-wide standardization of this protocol is tracked by `uibcdf/molsyssuite#27`.
MolSysViewer owns the noarch implementation and its release evidence; candidate identity,
staging/public separation, bootstrap rules, coordinate integrity and evidence retention
must converge on the shared contract instead of remaining a local convention.

The first hosted staging attempt, run `35475976799`, failed before upload. GH Run
Receptor 1.0.0 reduced the run to one root cause: conda-build selected Python 3.14.7 for
the host environment because the recipe said `python>=3.11` there, while the runtime and
project contract correctly said `python>=3.11,<3.14`. The package therefore refused its
own host interpreter during the recipe test. An independent staging-channel query found
no MolSysViewer 0.23.1 artefact, so build 0 remains unused rather than overwritten.

The host requirement now carries the same closed interval as `requires-python` and the
runtime requirement. The distribution guard parses host and run as separate sections;
either bound drifting now fails with a message naming that side of the recipe. The full
suite passes 2,067 tests with 13 accepted skips under 12 workers after the repair. A new
exact commit, not the failed attempt's SHA, is required for the next staging dispatch.

## State of the corrections

1. **Cause 2 — done** (2026-09-19). Environment files carry the runtime dependencies and
   their floors; guarded and mutation-verified.
2. **Cause 3 — done** (2026-09-19). `CI_e2e` installs the package; both build scripts
   resolve the version through one module; guarded and mutation-verified. The npm and
   conda consequences are uibcdf/molsysviewer#89.
3. **Gate 8 — done** (2026-09-19). The master plan now states that the workflow exists
   and has never passed.
4. **Cause 1 — active.** The staging mechanism is implemented and locally guarded. It
   closes only after the exact pair passes the hosted candidate gates, MolSysMT reaches
   the public channel with Python 3.11–3.13 support, and ordinary CI passes against it.
5. **The version test — done** (2026-09-19). The comparison is guarded on chosen
   versions; the statement about this checkout stays in the release gate.

None of the three repaired causes can be *confirmed* on hosted CI while cause 1 stands,
because no job reaches the point where they would show. They were verified locally and by
mutation; the hosted confirmation comes with gate 1, and this entry does not close before
it.

**Measured on `b4a119a4`, the commit that carries these fixes.** All three workflows still
fail, and every one of them now fails at environment creation with the same line:

```
molsysmt >=0.22.0 * does not exist (perhaps a typo or a missing channel).
```

Seven of seven `CI` jobs — the six matrix cells and the Qt pipeline — plus `CI_e2e` and
`Documentation notebooks`. Before, the 3.11 and 3.12 cells resolved an old MolSysMT and
failed later on a missing import, the 3.13 cells and Qt printed fifteen lines of solver
tree about Python ABIs, and `CI_e2e` failed on a missing file. Nine jobs, four stories,
none of them naming the cause. Now they say it in one line, and the one line is true:
this repository is waiting for a MolSysMT release. `MolSysSuite policy` and `Ruff Lint`
pass, as before.

## Acceptance

### New hosted evidence, 2026-09-24

Manual `Documentation notebooks` staging run `35997846329` successfully
installed the coordinated dependencies and reached notebook execution. It then
failed in `showcase/pockets.ipynb` because the Python pocket-blob API rejected
the frontend-supported plural iso options (uibcdf/molsysviewer#99), and in
`showcase/channels.ipynb` because the example still used the old `smoothing`
argument. Both have local fixes and successful notebook executions on the
`python-3.14-support` branch. The rerun `36016496850` passed every documented
notebook on exact commit `7c4e0cd968e9530033e35221683ca085fe1d37cd`.
That is a green staged-dependency documentation gate on the source branch,
not yet the required ordinary `main` gate against public packages.

Manual `CI_e2e` staging run `35998036249` installed its environment and built
the JavaScript harness. Chromium's 164.7 MiB download reached 100% within two
seconds, but browser installation emitted no further progress for over two
hours and never entered the tests. It was cancelled. The result is an
infrastructure/setup gap, neither an E2E pass nor a product E2E failure. Keep
headless browser E2E in hosted CI; retain visible-window/GPU checks as a
separate manual requirement. A diagnostic rerun, `36016496630`, bounded the
browser-install step to 15 minutes. Playwright reported a successful download
in two seconds, then stopped at `extracting archive` until the step timed out.
The E2E harness already selects `/usr/bin/google-chrome` by default, which the
GitHub-hosted Ubuntu image provides. Installing Playwright's separate Chromium
archive was unused by these tests and has now been replaced by an executable
check and logged Chrome version. A hosted rerun must reach and execute the
browser tests before this gate can be claimed.

The full staging-enabled `CI` rerun `36017021764` crossed the solver barrier
and passed its Qt pipeline, but all six Python matrix jobs failed in `Run
tests`. Linux/Python 3.13 reported 2,088 passes, 17 skips and seven failures:
the README examples lacked optional `mdtraj`; two information-table tests
lacked `jinja2`; two JS-build tests lacked `node_modules/esbuild` because
`npm ci` ran only after the Python suite; and the no-isolation wheel test
failed without exposing the captured build stderr. The other five matrix jobs
failed on the same README dependency boundary. The branch test environment
now carries `mdtraj`, `jinja2`, and the declared wheel build requirements,
installs npm dependencies before Python tests, and includes captured output
when the wheel build fails. The focused local slice passed 32 tests. This is
source readiness; a hosted rerun is still required.

- `CI`, `CI_e2e` and `Documentation notebooks` pass on `main` against the MolSysMT this
  package declares, not an older one the solver happens to find.
- Gate 8 says what is enforced.
- Causes 2 and 3 may close before cause 1. This entry closes with cause 1, and it may
  pass through `partial` on the way.
