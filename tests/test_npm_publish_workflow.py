"""Keep npm publication bound to one automatic release event."""

from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "npm-publish.yaml"


def test_npm_publisher_has_only_one_automatic_trigger():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    triggers = workflow[True]

    assert set(triggers) == {"push", "workflow_dispatch"}
    assert triggers["push"]["tags"] == ["*"]
    manual_tag = triggers["workflow_dispatch"]["inputs"]["tag"]
    assert manual_tag["required"] is True
    assert "default" not in manual_tag
