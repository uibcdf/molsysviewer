from __future__ import annotations

import molsysviewer.viewer.core as core_module
from molsysviewer import MolSysView


def test_frontend_context_action_error_sends_runtime_ack_and_smonitor(monkeypatch):
    view = MolSysView()
    view._ready = True  # noqa: SLF001
    sent: list[dict] = []
    emitted: list[dict] = []
    history_len = len(view._test_message_log)  # noqa: SLF001
    view.widget.send = lambda msg: sent.append(dict(msg))  # type: ignore[attr-defined]

    def fake_emit(entry, *, package_root=None, meta=None, extra=None):
        emitted.append({"entry": entry, "extra": dict(extra or {})})
        return {"entry": entry, "extra": extra or {}}

    monkeypatch.setattr(core_module, "emit_from_catalog", fake_emit)

    view._handle_frontend_event({  # noqa: SLF001
        "event": "interaction_context_action",
        "action": "delete_region",
        "tag": "missing-region",
    })

    assert sent == [
        {
            "op": "backend_error_occurred",
            "trigger_event": "interaction_context_action",
            "action": "delete_region",
            "error_type": "ValueError",
            "error_message": "No region found with tag 'missing-region'.",
        }
    ]
    assert len(view._test_message_log) == history_len  # noqa: SLF001
    assert emitted[0]["entry"]["code"] == "MOLSYSVIEWER-FRONTEND-ACTION-FAILED"
    assert emitted[0]["extra"]["operation"] == "frontend-interaction-action"
    assert emitted[0]["extra"]["failure_class"] == "frontend_backend_desync"
    assert emitted[0]["extra"]["evidence"]["tag"] == "missing-region"
