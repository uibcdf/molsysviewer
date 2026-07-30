# Import and message-cost audit

**Status:** resolved before 1.0.

This audit originally identified three classes of overhead:

1. repeated synchronization of the complete `initial_messages` trait while the
   frontend was not ready;
2. eager imports from `molsysviewer.__init__`;
3. avoidable disabled/enabled-path overhead in SMonitor, DepDigest, and
   PyUnitWizard.

All actionable findings are implemented:

- `d7bd3b0c` replays pending scene history once at frontend readiness instead of
  reassigning the full trait for every queued message;
- `0765ae80` makes the public MolSysViewer API lazy while retaining the public
  names;
- SMonitor's disabled and enabled paths were optimized in its own repository;
- PyUnitWizard now loads unit backends on demand.

The current `HistoryMixin._send()` records a message and sends it only when the
frontend is ready. It does not assign `widget.initial_messages`. The package
root uses `_LAZY_ATTRIBUTES` and PEP 562 materialization rather than eager
imports of the public surface.

This work is closed. New import or per-message performance claims require a new
measurement against the current code rather than reusing the historical
numbers.
