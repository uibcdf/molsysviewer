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

The [isolation receipt](../jupyter_buffer_isolation_receiving_20261111.json)
preserves complete-entry failure `471`: six stopped and five moving captures
pass, then the sixth moving Studio popup session reaches its unchanged
deadline. Four explicitly reduced controls pass cancellation and autonomous
timeout: moving setup/play/stop alone, one moving popup save, the complete
stopped prefix without moving saves, and all six moving saves without the
stopped prefix. Neither prefix independently reproduces the failure. These
controls cannot be combined into full-entry acceptance or a deterministic
pause/teardown diagnosis.

The later `477` child fails at the plain-kernel baseline before importing
MolSysViewer. Its outer supervisor is interrupted and retains its original
running record; recovery independently verifies unchanged inputs, removal of
ephemeral settings, the child's cleanup and no surviving exact-scope process.
No outer exit, resource peak or product result is inferred from that recovery.
Passive bounded readiness/draw diagnostics now preserve a failed held-reply
precondition without repairing frames or changing replies/deadlines; `477`
does not reach that diagnostic target.

Next isolate readiness immediately after the moving fixture's real stop and
transport teardown, before installing the held-reply control. Receive the
current frame, outstanding scientific queries, capture reservation and actual
native draw without a repair seek, fake reply, blanket pause or longer
deadline. Compare the live and retired owners before attributing the failure
to widget cleanup. If the receiver precondition is wrong, correct and guard it;
if the product cannot reach coherence, fix that owner and receive the full
entry. #315's consolidated gate and publication qualification remain open.

## Native prerequisite receiving — 2026-11-12

The [Movie migration receipt](../movie_legacy_receiving_20261112.json) also
receives two bounded prerequisites, without requalifying this actual-Jupyter
entry. The browser fixture's previous request/reply-only transport strands
scheduled comm sends until another browser request; the old-source control
fails and the corrected real-View scheduled-send guard passes. A closed browser
now detaches its receiver without killing the independently running Python
authority. Renderer capture keeps another native draw requested after a
rejected incoherent draw: metadata can become ready without changed geometry.
The idle-canvas unit guard receives that liveness correction independently.

Native source attempt `562` with 2 CPU / 4 GiB fails a moving popup save;
`563` with 4 CPU / 4 GiB progresses farther but fails a detached Studio save.
After the draw correction, `564` passes the complete isolated native scenario,
including six moving saves and the empty-frame/presentation controls. The
covering repetition `566` still fails the sixth moving save. Both complete
outcomes remain; the passing isolated entry and later successful prefixes do
not establish stable combined acceptance or a single cause for older traces.
Seven separate selected browser suites receive Movie, lifecycle, transport and
media scopes. No new actual Jupyter, native Qt, installed or human acceptance
is claimed. This issue remains active.
