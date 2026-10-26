"""Guard observed advisory ranges, including later body-parser findings."""

import json
from pathlib import Path

import yaml
from packaging.specifiers import SpecifierSet
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]

# Union of affected ranges reported by npm on 2026-10-13 for this dependency
# graph (uibcdf/molsysviewer#242). This offline regression guard complements
# the live registry audit; it cannot enumerate future or other-major advisories.
# body-parser 2.x also includes GHSA-27r3-jxmh-p828 (uibcdf/molsysviewer#266).
KNOWN_AFFECTED = {
    "body-parser": ">=2.0.0,<2.4.0",
    "brace-expansion": ">=2.0.0,<2.1.7",
    "compression": "<1.8.2",
    "form-data": ">=4.0.0,<4.0.6",
    "immutable": ">=5.0.0-beta.1,<5.1.8",
    "minimatch": ">=9.0.0,<9.0.7",
    "path-to-regexp": ">=8.0.0,<8.4.0",
    "proxy-addr": ">=1.1.0,<2.0.8",
    "qs": "<6.16.0",
}


def test_lockfile_excludes_observed_advisory_ranges_at_every_depth():
    lock = json.loads((ROOT / "molsysviewer/js/package-lock.json").read_text())
    affected = []
    for path, entry in lock["packages"].items():
        name = path.rsplit("node_modules/", 1)[-1]
        if name in KNOWN_AFFECTED and SpecifierSet(KNOWN_AFFECTED[name]).contains(
            Version(entry["version"]), prereleases=True
        ):
            affected.append(f"{path}@{entry['version']}")
    assert affected == [], affected


def test_live_registry_audit_is_required_before_browser_and_release_qualification():
    workflow = yaml.safe_load((ROOT / ".github/workflows/CI_e2e.yaml").read_text())
    steps = workflow["jobs"]["e2e"]["steps"]
    install = next(i for i, s in enumerate(steps) if s.get("run") == "npm ci")
    audit = next(i for i, s in enumerate(steps) if s.get("run") == "npm audit --audit-level=low")
    build = next(i for i, s in enumerate(steps) if "npm run build:harness" in s.get("run", ""))
    assert install < audit < build
    assert steps[audit]["working-directory"] == "molsysviewer/js"
    assert not steps[audit].get("continue-on-error", False)
