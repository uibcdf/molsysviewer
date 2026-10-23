"""A failed real addon state factory remains diagnosable and retryable."""

import pytest
from molsysviewer.addons import GlobalAddonsRegistry, ViewAddonsManager

from molsysviewer import AddonSpec, demo


def test_failed_state_factory_preserves_exception_and_can_retry():
    attempts = []
    original = RuntimeError("intentional factory initialization failure")

    def factory(view):
        count = view.whole.get(element="system", n_atoms=True)
        attempts.append(count)
        if len(attempts) == 1:
            raise original
        return {"n_atoms": count}

    host = GlobalAddonsRegistry()
    host.register(AddonSpec(name="factory-receiving", state_factory=factory))
    with demo["dialanine"] as view:
        manager = ViewAddonsManager(view, host)
        with pytest.raises(RuntimeError) as failure:
            getattr(manager, "factory-receiving")
        assert failure.value is original
        records = manager.lifecycle_failures()
        assert len(records) == 1
        assert records[0]["source"] == "lifecycle:factory-receiving.state_factory"
        assert "intentional factory initialization failure" in records[0]["reason"]
        state = getattr(manager, "factory-receiving")
        assert state["n_atoms"] > 0
        assert len(attempts) == 2
        assert getattr(manager, "factory-receiving") is state
        assert manager.lifecycle_failures() == []
