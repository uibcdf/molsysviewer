---
summary: Standalone HTML construction retains internally created Views and widget registrations.
issue: uibcdf/molsysviewer#324
status: partial
opened: 2026-11-07
closed:
severity: medium
verification: reproduced
area: [standalone, lifecycle, export]
guard: tests/test_standalone_view_ownership.py
normative:
blocked_by: []
supersedes: []
---

# Standalone HTML ownership

**Corrected and locally verified in working source; reviewed integration and
consolidated acceptance remain pending.** Repeated real HTML construction with
`None` or a native MolSys retains one unreturned View and two widget/comm
registrations per call. Four calls in each fresh-process control leave four
Views and eight registrations after collection. A borrowed View remains at its
original baseline. Closing only the internally created Views restores the
baseline, identifying an ownership failure rather than a global cleanup need.

The writer now releases a View it creates, on successful export and on error.
Caller-supplied Views retain their exact data, scene, callbacks and comms.
The demo gallery and CLI also release fresh Views obtained from DemoCatalog;
the nested HTML writer borrows those objects. Cleanup must preserve the
original writer/load error, adding a diagnostic note if cleanup also fails;
a cleanup-only failure remains observable. Already written files and unrelated
caller output are preserved.

The durable guard uses real demo systems, actual widget and comm registries,
filesystem/load failures, the default gallery, CLI and a real failing close
callback. Assertions occur before pytest's autouse cleanup, without forced
collection or a registry sweep. Its initial causal run fails four owned cases
while two borrowed controls pass. The corrected module passes **17 cases**;
the existing factory and selected HTML/CLI boundary checks pass **24 cases**.
These counts describe separate recorded selections, not overall plan progress.

Reusing the unchanged original probe in three fresh processes confirms zero
retained internally owned Views and unchanged registration baselines after all
four builds for empty, MolSys and borrowed inputs. Original red observations
remain in approved private custody. The
[sanitized receiving record](../standalone_html_ownership_receiving_20261107.json)
preserves the source/guard hashes, causal results and scope limits. This is
Python ownership evidence, not browser, visible Qt,
installed-package or final candidate qualification.

Related #316 concerns initialization failure in `new_view`; #318 concerns a
failed close blocking other cleanup. Neither alone covers this writer's
successful-return lifetime. This follow-up belongs to the A4/A6 boundary of
#315 and does not silently change its original 46-item denominator.
