"""Public setup commands and native-host claims must match distribution policy."""

import json
import re
import shlex
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SURFACES = (
    "README.md",
    "docs/content/user/introduction/installation.ipynb",
    "docs/content/user/troubleshooting/viewer_not_loading.md",
)


def _narrative(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    if path.endswith(".ipynb"):
        return "\n".join(
            "".join(cell["source"]) for cell in json.loads(text)["cells"] if cell["cell_type"] == "markdown"
        )
    return text


@pytest.mark.parametrize("path", SURFACES)
def test_public_installation_commands_use_published_conda_channel(path):
    """The obsolete PyPI command cannot resolve the required UIBCDF backend."""
    text = _narrative(path)
    # Include inline troubleshooting commands and continued shell blocks.
    text = text.replace("\\\n", " ")
    commands = re.findall(r"```bash\n(.*?)```|`([^`\n]+)`", text, re.DOTALL)
    package = re.compile(r"^molsysviewer(?:$|[<>=!])")
    found = False
    for block, inline in commands:
        for line in (block or inline).splitlines():
            tokens = shlex.split(line, comments=True)
            if not any(package.match(token) for token in tokens):
                continue
            if "install" not in tokens and "update" not in tokens and "create" not in tokens:
                continue
            found = True
            assert tokens[0] in ("conda", "mamba"), f"{path}: public route is not Conda: {line}"
            assert "-c" in tokens and "uibcdf" in tokens, f"{path}: required public channel missing: {line}"
    assert found, f"{path}: no public installation/update command"


@pytest.mark.parametrize("path", SURFACES[:2])
def test_core_support_does_not_certify_native_hosts(path):
    """Noarch/Python coverage must not turn into a supported Qt/remote claim."""
    text = _narrative(path)
    rows = [line.lower() for line in text.splitlines() if line.startswith("|")]
    core = next(row for row in rows if "core python api" in row)
    qt = next(row for row in rows if "qt desktop host" in row)
    remote = next(row for row in rows if "remote sessions" in row)
    for platform in ("linux", "arm64", "macos apple silicon", "windows"):
        assert platform in core
    assert "3.11–3.14" in core
    assert "experimental" in qt and "separate qualification" in qt
    assert "unsupported preview" in remote and "post-1.0" in remote
