---
summary: Diagnose failed consolidated Jupyter capture after moving saves.
issue: uibcdf/molsysviewer#344
status: active
opened: 2026-11-11
closed:
severity: medium
verification: measured
area: [jupyter, capture, lifecycle, performance]
guard: tests/test_jupyter_live_capture.py::test_live_jupyter_work_files
normative:
blocked_by: []
supersedes: []
---

# Consolidated Jupyter capture — receiving reopened

The earlier [font-content correction](../archive/jupyter_moving_capture_residual_uploads.md)
and its exact-source receiving remain historical evidence. This reopening does
not establish repeated font uploads, invalidate that bounded correction or
justify changing Mol* and its adapter without new causal evidence.

On base `b2b41c00` plus the #356 widget-controller cleanup, the unchanged
actual-Jupyter guard fails in two different scopes. `464` uses 2 CPU / 4 GiB:
six stopped captures/restores pass; the first moving Studio state save reaches
the unchanged ten-second deadline. The connected visible canvas keeps playing,
Python is ready/open and real interaction/dynamic-region replies lag the
current frame. Its selected inputs remain unchanged, peak summed owned RSS is
2943.9 MiB, no resource stop occurs and all 19 owned processes retire.

The explicit capacity comparison `466` uses the former qualification ceiling
of 8 CPU / 6 GiB. Six stopped and all six moving captures pass, but the later
cancel-late-reply setup times out after 30 seconds waiting for an actual
held visual-state reply. Cancellation itself and the subsequent autonomous
timeout case are not received. Its 5956 selected inputs remain unchanged,
peak summed owned RSS is 3362.8 MiB, no resource stop occurs and all 19 owned
processes retire. Both runs retain a 6.5-GiB global reserve and zero own swap.

These are failed complete entries. Their successful prefixes cannot be
combined into acceptance. CPU sensitivity is measured; it does not prove the
precise product/fixture owner or a causal relation to #356's cleanup.
The [receipt](../widget_controller_release_receiving_20261111.json) preserves
both traces and keeps the passing controller-release regression separate.

Next isolate readiness immediately after the moving fixture's real stop and
transport teardown, before installing the held-reply control. Receive the
current frame, outstanding scientific queries, capture reservation and actual
native draw without a repair seek, fake reply, blanket pause or longer
deadline. Compare the live and retired owners before attributing the failure
to widget cleanup. If the receiver precondition is wrong, correct and guard it;
if the product cannot reach coherence, fix that owner and receive the full
entry. #315's consolidated gate and publication qualification remain open.
