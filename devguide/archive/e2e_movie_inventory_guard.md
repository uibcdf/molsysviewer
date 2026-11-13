---
summary: E2E inventory guard still expects 53 suites after Movie additions.
issue: uibcdf/molsysviewer#373
status: resolved
opened: 2026-11-13
closed: 2026-11-13
severity: medium
verification: reproduced
area: [tests, movies, ci]
guard: tests/test_e2e_reliability.py::test_e2e_runner_inventory_matches_every_scientific_suite
normative:
blocked_by: []
supersedes: []
---

# Resolved: E2E registration count after Movie growth

## What

The existing offline inventory guard fails with `assert 62 == 53`. Nine
Movie entries were added to the 53 existing browser suites, the canonical
runner and the build route, without updating the deliberately frozen count.
The defect already exists at source
`185b0ed7fdfc75dd20306edf8c989a7c87ac9f2b`; it is independent of the #372
native Mol* dependency change that revealed it.

## How

Run `python -m pytest --receptor=llm
tests/test_e2e_reliability.py::test_e2e_runner_inventory_matches_every_scientific_suite`
with the explicit development interpreter. Controlled receiving `690` retains
one failure, the native exit/JUnit and unchanged inputs. Complete all-state
issue pagination was checked before filing.

## Correction and acceptance

The expected count first becomes 62, identifying the nine Movie scopes, then
63 when #377 adds the mandatory persistent Studio entry. Exact source/runner/
build set equality and every core/remote registration remain. The existing
selector passes in `693`; the complete eight-case runner module and all entry
builds pass in `705`. Its set/count assertions reject a missing or unregistered
scientific suite. No operation deadline or scientific assertion changes in this
correction. Registration is not browser, installed, platform or human acceptance.
