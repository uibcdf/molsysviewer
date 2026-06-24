# Proposal: Remove Deprecated `W503` Rule Selector from Ruff Configuration

## Abstract

We propose removing the deprecated `W503` rule selector from the `[tool.ruff.ignore]` section of `pyproject.toml` in `molsysviewer`. This rule is not recognized by modern versions of Ruff, causing linting and formatting runs to crash with configuration errors. Removing it restores compatibility with newer Ruff releases.

---

## The Problem

When running modern versions of `ruff` on the `molsysviewer` repository, the command terminates with the following error:

```
Cause: Failed to parse /home/diego/repos@uibcdf/molsysviewer/pyproject.toml
Unknown rule selector: W503
```

This occurs because `W503` (line break before binary operator) is a PEP 8 warning from flake8. Ruff does not implement this check, and in newer versions, specifying an unknown or deprecated rule in `select` or `ignore` results in a fatal parsing error, preventing the linter from running at all.

---

## Proposed Solution

Modify `pyproject.toml` (specifically [pyproject.toml:L96-100](file:///home/diego/repos@uibcdf/molsysviewer/pyproject.toml#L96-100)) to remove the `"W503"` line from the `ignore` list.

### Before:
```toml
ignore = [
  "E203",  # compatible with Black (spaces before ':')
  "W503",  # compatible with Black (line break before operator)
]
```

### After:
```toml
ignore = [
  "E203",  # compatible with Black (spaces before ':')
]
```

Since Ruff inherently handles line breaks around binary operators and conforms to PEP 8 / Black formatting rules, removing this explicit ignore selector has no impact on existing code styling checks.

---

## Benefits

* **Restores Linter Compatibility**: Developer environments using modern Ruff versions can successfully run formatting and lint checks without configuration parser failures.
* **Streamlined CI/CD**: Prevents potential continuous integration build failures when upgrading Python dependencies and toolchains.
