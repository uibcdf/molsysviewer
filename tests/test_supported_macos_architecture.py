"""Guard the prospective macOS support boundary in hosted workflows."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def test_macos_ci_uses_the_explicit_apple_silicon_runner():
    for name in ("CI.yaml", "ci-python-314-source-pair.yaml"):
        text = (WORKFLOWS / name).read_text(encoding="utf-8")
        workflow = yaml.safe_load(text)
        assert "macos-15-intel" not in text
        assert "macos-latest" not in text
        assert "macos-15" in text
        assert isinstance(workflow["jobs"], dict)


def test_noarch_publication_does_not_request_an_intel_build():
    text = (WORKFLOWS / "build_and_upload_conda_packages.yaml").read_text(encoding="utf-8")
    assert text.count("platform_osx-64: false") == 2
    assert "platform_osx-64: true" not in text
