"""Exercise declared installer routes through the actual dependency provider."""

import pytest
from depdigest import check_dependency
from molsysviewer._depdigest import DOC_URL, LIBRARIES
from molsysviewer._private.exceptions import LibraryNotFoundError


@pytest.mark.parametrize("name", ["molsysmt", "pyunitwizard", "smonitor", "depdigest", "argdigest"])
def test_suite_dependency_diagnostic_uses_the_qualified_conda_route(name):
    entry = LIBRARIES[name]
    assert entry["pypi"] is None
    with pytest.raises(LibraryNotFoundError) as caught:
        check_dependency(
            "molsysviewer_intentionally_absent_dependency_probe",
            pypi_name=entry["pypi"],
            conda_name=entry["conda"],
            conda_channel=entry["channel"],
            doc_url=DOC_URL,
            exception_class=LibraryNotFoundError,
        )
    message = str(caught.value)
    assert f"conda install -c uibcdf {name}" in message
    assert "pip install" not in message
    assert DOC_URL in message
