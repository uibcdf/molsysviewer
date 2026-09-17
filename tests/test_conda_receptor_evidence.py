"""Guarding structured gh-run-receptor evidence in the Conda publisher."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/build_and_upload_conda_packages.yaml"
UPLOAD_ACTION = "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f"


def test_noarch_conda_publisher_retains_structured_producer_evidence():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["conda_deployment_with_new_tag"]["steps"]
    build = next(step for step in steps if step.get("id") == "conda_build_and_upload")
    evidence = next(step for step in steps if step.get("name") == "Upload structured producer evidence")

    assert build["uses"] == "uibcdf/action-build-and-upload-conda-packages@v2.1.0"
    assert "evidence_matrix_index" not in build["with"]
    assert evidence["if"] == ("${{ always() && steps.conda_build_and_upload.outputs.evidence_path != '' }}")
    assert evidence["uses"] == UPLOAD_ACTION
    assert evidence["with"] == {
        "name": "${{ steps.conda_build_and_upload.outputs.evidence_artifact_name }}",
        "path": "${{ steps.conda_build_and_upload.outputs.evidence_path }}",
        "if-no-files-found": "error",
        "retention-days": 7,
    }
