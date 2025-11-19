import re

import molsysviewer


def test_print_version_outputs_version(capsys):
    """Import works and __print_version__ emits the expected string."""
    version = molsysviewer.__version__
    assert isinstance(version, str) and version.strip()

    molsysviewer.__print_version__()

    captured = capsys.readouterr().out
    assert re.search(rf"MolSysViewer version {re.escape(version)}", captured)
