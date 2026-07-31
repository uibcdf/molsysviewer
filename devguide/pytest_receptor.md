# Compact test output with pytest-receptor

MolSysViewer's Python test suite can be run through
[`pytest-receptor`](https://github.com/uibcdf/pytest-receptor), which renders
pytest's output compactly and truth-preservingly for a coding agent. It applies
only to the Python `pytest` runs (the JS/TS unit and Playwright suites are
unaffected) and changes nothing about whether tests pass.

## Running it

Following the test-run discipline in the root `AGENTS.md` (rule 12):

```bash
pytest --receptor=llm tests/test_foo.py -x    # the specific file first
pytest --receptor=llm tests/                  # then the full suite once
```

MolSysViewer invokes tests as bare `pytest`, so the receptor's default `rerun:`
commands are already executable here — no `receptor_rerun_command` is needed.

Do **not** combine it with `--tb=no` or `--tb=line`: those delete the frame
evidence the compact report needs to point at the failure. In particular, drop
the `--tb=no` from the rule-12 full-suite check when using `--receptor=llm`.

## Use it by default (updated 2026-07-31)

**`--receptor=llm` is the default runner.** It saves a substantial amount of
context, and its fidelity is now trusted. Do not cross-check every run against
plain `pytest`.

Run plain `pytest` **only when there is a specific suspicion** that the compact
report is hiding or missing something. If the comparison shows the receptor was
indeed at fault, that is a report worth filing upstream — see below.

*(This section previously said "normal `pytest` remains the authority". That was
the evaluation-period rule and is superseded: routine double-running costs
tokens and buys nothing once the tool is trusted.)*

## Report anything wrong or missing

Feedback goes into the `pytest-receptor` repository, not an issue tracker:

- **Something wrong** — bad output, a crash, or a disagreement with pytest about
  a run's outcome or counts (urgent): `pytest-receptor/devguide/pending_bugs/`
- **Something to improve** — a rough edge or a feature you need:
  `pytest-receptor/devguide/pending_proposals/`

The most valuable report is a run where the compact output was **not enough to
act on** — where you had to open the on-disk report, read a source file, or run
pytest again to understand a failure.

## Full note

The maintained collaborator note upstream —
[`for_collaborators.md`](https://github.com/uibcdf/pytest-receptor/blob/main/devguide/for_collaborators.md)
— is the fuller reference for what it does, how to read its output, and the
guarantees it makes.
