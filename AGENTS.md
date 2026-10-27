# Guidelines for AI Agents

## Mandatory MolSysSuite instructions

Read and follow `MOLSYSSUITE_GUIDE.md` before working in this repository.

Within their stated scope, its common rules take precedence over this file
and any nested `AGENTS.md`. Local instructions may refine them; deviations
require the documented policy exception process.

The synchronized guide is owned by `uibcdf/molsyssuite`. It includes the
[reusable-tool ownership rules](MOLSYSSUITE_GUIDE.md#modular-reusable-tools)
and [working-instruction rules](MOLSYSSUITE_GUIDE.md#durable-working-instructions).
For work under `devguide/`, also read `devguide/AGENTS.md` and its local
reporting protocol. Keep repository-specific instructions below.

## Local working context

This document provides critical instructions for all AI assistants or automation tools contributing to this repository.

## Development with the principal maintainer

For changes authorized by the principal maintainer, use reviewed commits and
direct pushes to `main`. Do not open pull requests unless the user requests one.
Keep the applicable validation and CI evidence, synchronize remote changes, and
preserve unrelated local work before integrating or publishing commits.

For local development with the principal maintainer, use the Conda environment
`molsyssuite@uibcdf_3.14`. Select its interpreter explicitly or activate it for
each command; do not rely on the shell's default `python`. Separate installed
artifact qualification environments retain their own recorded provenance.

Read `MOLSYSSUITE_GUIDE.md` before development. It is the synchronized, read-only
suite-governance guide owned by `uibcdf/molsyssuite` and routes shared policies,
cross-component feedback, and issue ownership.

## 🚫 Do *Not* Modify Generated Files

The following files **must not be edited manually**:

* `molsysviewer/viewer.js`
* `molsysviewer/viewer.js.map`

These files are **build artifacts** generated automatically from the TypeScript sources located in the `js/` directory. Any manual edits will be overwritten and may corrupt the build process.

## 🚫 Do *Not* Read Generated Files

The following files **must not be readed** to avoid oversized context and irrelevant diffs:

* `molsysviewer/viewer.js`
* `molsysviewer/viewer.js.map`
* `docs/_static/views/*.html`

These files are **build artifacts** generated automatically from the TypeScript sources located in the `js/` directory. Any manual edits will be overwritten and may corrupt the build process.
The content of these files is not relevant for understanding or modifying the viewer's logic.
Their content is redundant with the TypeScript source files. Read only the TypeScript source files.
The HTML files under `docs/_static/views/` are auxiliary exports for documentation embeds and do not add
developer-relevant context beyond the docs sources.

## ✔️ Source of Truth

The authoritative JavaScript/TypeScript sources live here:

```
js/src/
    index.ts
    managers/
    shapes/
    plugin/
    messages/
```

**Only these files should be edited** when modifying frontend logic. After changes, the build system must be executed to regenerate `viewer.js` and `viewer.js.map`.

## 🛠️ Build Process (summary)

1. Edit TypeScript files inside `js/src/`.
2. For development rebuilds, run `npm run build:runtime` from
   `molsysviewer/js/`. This regenerates the runtime bundle without rewriting
   JS package version metadata.
3. Use `npm run build` only for release/packaging flows where syncing the JS
   package version from Python is intentional. It runs
   `sync-python-version.mjs` first and may rewrite
   `molsysviewer/js/package.json`, including `pythonVersion`.
4. The bundler (esbuild) produces updated versions of:

   * `molsysviewer/viewer.js`
   * `molsysviewer/viewer.js.map`

AI agents must never write directly to these generated outputs.
If `npm run build` is used accidentally in a dirty working tree and only
`pythonVersion` changes to a local version such as `X.Y.Z+...dirty`, do not
commit that metadata churn; use `npm run build:runtime` for normal TS
validation work instead.

## 🤖 General Development Rules for AI Agents

1. Always prefer editing TypeScript source files over build artifacts.
2. Do not create duplicate build outputs.
3. Preserve the structure of the `molsysviewer/` package.
4. Maintain consistency with the project's developer documentation under `docs/content/developer/`.
5. Docs: follow `docs/content/developer/documentation/web/build_and_layout.md`; use static views in `_static/views/` for embeds.
6. When in doubt, **ask before modifying files outside `js/src/`**.
7. MolSys payload schema (Python → TS): top-level `structures` list, each with `coordinates` (Å), optional `box` as three vectors (Å), and `time`. Do not reintroduce legacy names like `positions` or `frames`.
8. Tests should avoid mocks: use the real demo viewers in `molsysviewer.demo` (`dialanine`, `pentalanine`, `tctim`, `chicken_villin_HP35`) to build regression/unit tests.
9. If a specific local setup shows a MolSysMT/Numba cache failure, document the exact traceback before adding an environment workaround. Do not assume `NUMBA_CACHE_DIR` overrides are required by default.
10. JS/TS tests:
    - Unit tests in `molsysviewer/js/tests/unit` (run with `npm run test:js`, coverage with `npm run coverage:js`).
    - E2E in `molsysviewer/js/tests/e2e` (headless Playwright against real Mol*). `npm run test:e2e` runs all suites through one shared Chromium process. The hosted `.github/workflows/CI_e2e.yaml` and the strict 1.0 gate run `test:e2e:core`: all non-remote browser suites. The remote-session feature remains a post-1.0 preview, not a 1.0 release gate (`uibcdf/molsysviewer#100`). `test:e2e:portable` retains core plus remote client/input scenarios; `test:e2e:remote-portable` selects those two remote scenarios; `test:e2e:server-gpu` selects the managed render-worker scenario for a qualified GPU host. `test:e2e:all` retains all suites. Exclusion from the core lane is not a passing remote result. You can force a local Chrome/Chromium with `PW_CHROMIUM_BIN=/path/to/chrome`. Browser launch or WebGL2 failure is an error by default; only an explicit `E2E_ALLOW_SKIP=1` opts out, and an opt-out is not validation. A stalled browser install is a CI provisioning failure, not evidence about the product. Visible-window Qt/GPU observations for the local standalone host remain separate manual release evidence. Do not substitute xvfb/mesa for those observations.
11. The `sandbox/` directory is a scratch area for developer experiments. Changes there may be committed without review, and should not drive architectural decisions or test expectations.
12. **Test-run discipline**: diagnose the full traceback and fix the root cause
    before rerunning. Start with the affected test file, then broaden to the full
    suite when the changed boundary or required gate warrants it. Retain still-
    applicable results; repeat a full gate when a new fix/input or unresolved
    failure invalidates it. Documentation-only work uses its scoped checks.
13. For TypeScript runtime validation during development, prefer
    `npm run build:runtime` over `npm run build`. The latter is a
    release/packaging command because it synchronizes package versions from the
    Python `versioningit` output.
14. Python test rendering follows `PYTEST_RECEPTOR_GUIDE.md` and the common
    developer-tool policy; retain native outcomes and diagnostic evidence.

## The developer guide (`devguide/`)

[`devguide/AGENTS.md`](devguide/AGENTS.md) governs that directory and refines this file
there. The rule worth knowing before opening it: **`archive/` and `audits/` are history,
not instructions.** Read them through
[`devguide/archive/README.md`](devguide/archive/README.md) and
[`devguide/audits/README.md`](devguide/audits/README.md) — one line per document, saying
what it decided — and open a document itself only for a question you can name, such as a
contract pointing at it for its rationale, a decision being reopened, or a claim that
needs its evidence. Asked to "read the devguide", that is 23 % of it you do not read.

## Local reporting tools

Read `devguide/reporting_protocol.md` for the component's record schema and paths.
`python devtools/devguide_index.py` generates queue indexes from front matter;
run it with `--check` to verify them. `tests/test_reporting_protocol.py` protects
the offline record/index contract. Maintain the specialized `archive/`/`audits/`
reading and content rules in `devguide/AGENTS.md`.

## Citation and preserved releases

- Read `devguide/release_and_citation.md` before preparing or publishing a release.
- `CITATION.cff` is the canonical user-facing citation record. `.zenodo.json` owns
  Zenodo-specific metadata and takes precedence during GitHub ingestion.
- The stable project DOI is the MolSysViewer concept DOI
  `10.5281/zenodo.18072956`. General public surfaces use it; an exact scientific
  workflow cites the distinct version DOI created by Zenodo.
- A Git tag alone is not a preserved release. Publish a GitHub Release and verify
  Zenodo ingestion before declaring the citation lifecycle complete.
- Run `python devtools/validate_citation.py --expected-version X.Y.Z` before tagging.
  Never move a published tag or DOI to repair metadata.

## Developer documentation (where to look first)

Use `docs/content/developer/index.md` as the entrypoint.

Common topics

- Setup: `docs/content/developer/dev_setup.md`
- Repo map: `docs/content/developer/repo_structure.md`
- JS/TS workflow: `docs/content/developer/js_workflow.md`
- Python ↔ TS contracts: `docs/content/developer/protocol_and_payloads.md`
- Public API and stability: `docs/content/developer/public_api.md`
- Regions/layers semantics: `docs/content/developer/regions_layers.md`
- Debugging: `docs/content/developer/debugging.md`
- Docs workflow + RTD parity: `docs/content/developer/docs_workflow.md`
- Releasing/version sync: `docs/content/developer/releasing.md`
- Configuration surface (planned/stub): `docs/content/developer/configuration.md`
- Demo systems for tests/docs: `docs/content/developer/demo_systems.md`

## 📌 Why This Matters

Editing generated files breaks:

* reproducibility,
* version control clarity,
* build determinism,
* debugging and maintenance workflows.

Follow these rules to ensure the viewer remains stable and maintainable.

## Mol* Source Context

When working on MolSysViewer, you MUST assume that the full Mol* (molstar) source tree is available locally under: `src_molstar`
This means:

- You should NOT treat Mol* as a black box.
- You may reason about internal Mol* APIs, viewer behaviors, render pipelines, geometry builders, representation logic,
  and state updates by referencing the local source code.
- When planning, debugging, or proposing refactors in JavaScript/TypeScript, refer to the Mol* source when clarity or
  correctness depends on understanding internal implementations.
- This context applies ONLY to work inside the MolSysViewer repository.

## External Tooling Guides (Required for Development)

These guides are required reading for anyone developing this library. They describe how external tools must be used here.

- `SMONITOR_GUIDE.md` — Required guide for SMonitor integration and diagnostics.
- `ACKREDIT_GUIDE.md` — Required guide for optional scientific attribution and citation
  reporting.
- `GH_RUN_RECEPTOR_GUIDE.md` — Required guide for compact, truth-preserving GitHub Actions diagnostics.
- `PYTEST_RECEPTOR_GUIDE.md` — Required guide for compact, truth-preserving pytest output
  in local and hosted development.

## Core visualization and add-on ownership

Apply [the product boundary](devguide/core_and_addon_boundary.md) when designing
features, public APIs, Studio controls or add-ons. Core serves visualization and
exploration, including qualified calculations that directly create/configure
visual content. Additional scientific analysis, preparation and molecular editing
tools belong to the owning add-on/scientific library. Keep scientific parameters
explicit, results separate from representations and Python APIs headless and
composable. Do not introduce hidden molecular preparation or infer automatic
observation of arbitrary MolSys edits. Document ownership, effects and actual
availability; distinguish source support from published package compatibility.
For the MolSysMT tools add-on, follow the accepted expert-API requirements in
[its separate plan](devguide/molsysmt_tools_addon_plan.md): mirror scientific
module/function paths with the current primary MolSys implicit; design GUI
tasks for nonprogrammers without narrowing the expert API.
Keep addon usage/capability references in the owning component. Viewer documents
addon management, creation and the catalogue; independent authors request
catalogue inclusion through a Viewer issue. Follow
[the documentation ownership rule](devguide/core_and_addon_boundary.md#add-on-documentation-and-catalogue-ownership).

## Registered integration guides

Read the registered consumer guides when working on their respective boundaries:

- `DEPDIGEST_GUIDE.md`
- `ARGDIGEST_GUIDE.md`
- `PYUNITWIZARD_GUIDE.md`
