"""Guarding structured gh-run-receptor evidence in the Conda publisher."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/build_and_upload_conda_packages.yaml"
UPLOAD_ACTION = "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f"


def test_noarch_conda_publishers_retain_structured_producer_evidence():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["conda_deployment_with_new_tag"]["steps"]
    for build_id, evidence_name in (
        ("conda_staging", "Upload staging producer evidence"),
        ("conda_release", "Upload release producer evidence"),
    ):
        build = next(step for step in steps if step.get("id") == build_id)
        evidence = next(step for step in steps if step.get("name") == evidence_name)

        assert build["uses"] == "uibcdf/action-build-and-upload-conda-packages@v2.1.0"
        assert "evidence_matrix_index" not in build["with"]
        assert evidence["if"] == f"${{{{ always() && steps.{build_id}.outputs.evidence_path != '' }}}}"
        assert evidence["uses"] == UPLOAD_ACTION
        assert evidence["with"] == {
            "name": f"${{{{ steps.{build_id}.outputs.evidence_artifact_name }}}}",
            "path": f"${{{{ steps.{build_id}.outputs.evidence_path }}}}",
            "if-no-files-found": "error",
            "retention-days": 7,
        }


def test_staging_closes_the_dependency_cycle_without_weakening_the_package_test():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["conda_deployment_with_new_tag"]["steps"]
    checkout = next(step for step in steps if step.get("uses") == "actions/checkout@v4")
    identity = next(step for step in steps if step.get("name") == "Validate the immutable candidate identity")
    staging = next(step for step in steps if step.get("id") == "conda_staging")
    release = next(step for step in steps if step.get("id") == "conda_release")

    assert checkout["with"]["ref"] == "${{ inputs.candidate_sha || github.event.release.tag_name }}"
    assert 'test "$(git rev-parse HEAD)" = "$CANDIDATE_SHA"' in identity["run"]
    assert staging["if"] == "github.event_name == 'workflow_dispatch'"
    assert staging["with"]["label"] == "staging"
    assert release["if"] == "github.event_name == 'release'"
    assert release["with"]["label"] == "main"
    assert "--no-test" not in staging["with"]["conda_build_args"]
    assert "--no-test" not in release["with"]["conda_build_args"]
    assert "uibcdf/label/staging" in WORKFLOW.read_text(encoding="utf-8")
