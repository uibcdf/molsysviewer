# Demo systems

Use demo systems for:

- reproducible docs examples,
- unit/integration tests,
- quick manual checks.

## Where they live

- `molsysviewer.demo` exposes a small set of built-in demo viewers.

## Why this matters

Demo systems keep tests deterministic.
They also avoid large external downloads in CI and docs builds.

## Recommended usage

- Prefer demos over mocks in tests.
- Prefer demos over remote PDB downloads in docs tutorials.

