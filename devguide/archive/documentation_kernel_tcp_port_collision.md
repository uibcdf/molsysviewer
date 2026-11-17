---
summary: Qualify Linux documentation kernels after an observed TCP bind collision.
issue: uibcdf/molsysviewer#401
status: resolved
opened: 2026-11-17
closed: 2026-11-17
severity: medium
verification: measured
area: [ci, documentation, jupyter, lifecycle]
guard: tests/test_source_workflow_coverage.py
normative:
blocked_by: []
supersedes: []
---

# Documentation kernel transport

**Resolved in the Linux source workflow:** an explicit, task-local standard
Jupyter IPC route passes the complete unchanged notebook corpus; ordinary
user transports remain selected by their own environment.

Full source43823224361 fails showcase/channels.ipynb before any notebook
cell: ipykernel's shell TCP bind returns `Address already in use`, followed
by `Kernel died before replying to kernel_info`. The original seven ZIPs
are hash-verified and retained. This is not evidence of a Viewer/MolSysMT
scientific error or #615's original unknown event. The traceback establishes
the occupied bind, not which process acquired that port.

Linux source CI now explicitly selects standard Jupyter IPC through a
temporary nbconvert configuration. Every nbconvert process gets an absolute,
short, UUID-qualified socket prefix in its private task directory. That
directory is retired on every shell exit. The existing four-worker executor,
all25 notebooks, scientific cells and failure semantics remain unchanged.
Other hosts and ordinary users retain their selected kernel transport; no
second port allocator or blind retry is added to Viewer.

Private1000 demonstrates that Jupyter's default relative IPC prefix does not
connect when nbconvert and its kernel use different working directories.
Private1001's absolute route executes all four probes but the provenance
guard rejects the active prefix's7.3 kernel. A unique private kernelspec
corrects that selection. Final1002 receives four actual isolated7.4 kernels
with distinct IPC endpoints and process identities through the unchanged
executor. It passes under 2 CPU / 2 GiB; all ten owned processes retire.
Corpus receiving `1003` then passes all 25 unchanged science notebooks through
the same four-worker executor in 79.68 seconds under 4 CPU / 4 GiB. Each
executed code fingerprint still matches its source and completion marker;
all 9,997 selected inputs remain fixed and all 54 owned processes retire.
The 81 source-workflow/ecosystem guards and scoped Ruff checks pass in `1006`.
The original `1005` failure exposes a second literal command expectation;
both guards now retain the complete final executor command while protecting
the IPC configuration and cleanup. No test selection or failure handling is
relaxed. The [current receipt](../camera_peer_and_ipc_receiving_20261117.json)
retains the original negatives and custody. This closes the explicit Linux
IPC route; it does not repair Jupyter's general TCP allocation algorithm or
qualify another host, hosted replacement or final installed candidate.
