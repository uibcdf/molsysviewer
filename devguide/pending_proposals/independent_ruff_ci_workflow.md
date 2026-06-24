# Proposal: Independent Ruff CI Workflow

**Status:** pending
**Owner:** MolSysViewer
**Related proposals:** `remove_w503_ruff_ignore.md`
**Related precedent:** TopoMT `.github/workflows/ruff.yaml`

## Purpose

MolSysViewer declares and configures Ruff, but no active GitHub Actions workflow
executes it. The Python and JavaScript test workflows therefore do not prevent
Python lint regressions.

## Current State

- `pyproject.toml` declares both Ruff and Black.
- Ruff configuration selects broad `E`, `W`, `F`, `I`, and `B` rule families.
- The configuration includes the unsupported `W503` ignore, which prevents
  modern Ruff versions from parsing the configuration. The pending
  `remove_w503_ruff_ignore.md` proposal must be resolved first.
- The current CI workflow executes pytest and JavaScript tests, but no Python
  lint or formatting check.

## Proposed Change

After removing the invalid `W503` selector, add a dedicated
`.github/workflows/ruff.yaml` workflow with one Ubuntu job.

The first enforced rule set should be deliberately narrower than the current
broad Ruff configuration and contain only correctness-oriented checks that have
been made clean:

```bash
ruff check molsysviewer --select F821,F822,F823,F841,B006,B023
```

The workflow should:

- run on pull requests and pushes to `main` affecting Python source,
  `pyproject.toml`, or the workflow itself;
- support `workflow_dispatch`;
- use a bounded Ruff version range;
- run independently from the Python test matrix and JavaScript workflows;
- avoid enforcing formatting in the first phase.

## Required Sequence

1. Resolve `remove_w503_ruff_ignore.md` so modern Ruff can parse
   `pyproject.toml`.
2. Run the critical rule set locally and correct its violations.
3. Add the independent workflow and require it on pull requests.
4. Evaluate broad `E`, `W`, `I`, and `B` enforcement separately.
5. Decide separately whether Ruff becomes the sole formatter and Black can be
   removed.

## Acceptance Criteria

- Modern Ruff parses the canonical configuration.
- The documented critical command passes from a clean checkout.
- The independent workflow passes on `main` and fails on an introduced critical
  lint violation.
- Linting runs once per relevant revision, not once per CI matrix entry.
- Existing Python, JavaScript, and end-to-end workflows remain unchanged.

## Non-Goals

- Enforcing all currently selected Ruff rules immediately.
- Replacing Black without a separate formatting migration.
- Mixing lint failures with test or JavaScript build failures.
