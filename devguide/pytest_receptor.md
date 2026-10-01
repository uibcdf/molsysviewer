# Compact Python test output

MolSysViewer uses the published **pytest-receptor 1.2.0** for Python tests.
The pin is shared by the development extra and the development, main-test and
Python 3.14 source-pair Conda environments. It is a developer tool, not a
runtime dependency of MolSysViewer. The canonical integration contract is
`PYTEST_RECEPTOR_GUIDE.md`.

## Local work

Follow the test-run discipline in root `AGENTS.md`: run the specific test file
first, fix a diagnosed failure before rerunning, then run the full suite once.

```bash
python -m pytest --receptor=llm -o 'receptor_rerun_command=python -m pytest' tests/test_foo.py -x
python -m pytest --receptor=llm -o 'receptor_rerun_command=python -m pytest' tests/
```

Do not combine compact output with `--tb=no` or `--tb=line`; those remove the
failure frames the report needs. The native pytest exit code and test results
remain authoritative. Routine double execution with plain pytest is not
required. Inspect the native report or rerun a specific failing test with human
output when there is a concrete diagnostic gap or suspected reporting error.

## Hosted tests

Every maintained pytest command in `CI.yaml` and the Python 3.14 source-pair
workflow uses `--receptor=ci`. Each job records and checks the installed tool
version before running tests. Keep the Python matrix, full suite, Qt selectors,
coverage XML and JUnit XML unchanged when changing output profiles. Configure
`receptor_rerun_command=python -m pytest` explicitly so emitted rerun commands
use the same environment's interpreter. JavaScript and browser tests retain
their native runners.

`tests/test_python_ecosystem_contract.py` guards the exact published pins,
profiles, executable rerun commands, selectors and coverage/JUnit configuration.
A workflow configuration is not a successful hosted result: review the exact
commit, executed test steps and native conclusions separately.

## Actions inspection and upstream feedback

Use the published GH Run Receptor and `.github/gh-run-receptor.yaml` for the
first inspection of a run. Native GitHub steps, logs and conclusions settle an
incomplete or ambiguous compact report. A compact success is not release
approval. The provider contract is `GH_RUN_RECEPTOR_GUIDE.md`.

Report a wrong verdict, crash, missing diagnosis, or proposed improvement by
opening an issue in `uibcdf/pytest-receptor` first, including the installed
version, command, exit code and minimal observed evidence. Its reporting
protocol governs any accompanying provider-side developer-guide record.
Cross-repository references use the issue identity.
