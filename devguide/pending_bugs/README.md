# Pending Bugs

This directory contains confirmed or reproducible defects that affect current
MolSysViewer behavior. Bug reports are evidence and implementation queues, not
future API proposals.

Each report should state the affected public contract, reproduction, cause,
recommended correction, and acceptance tests. Move resolved reports to an
archive only after the implementation and regression tests are complete.

## Current triage

- `missing_argdigest_color_digesters.md` — public color operations emit
  `DigestNotDigestedWarning` for their declared `value_range` and `replace`
  arguments.
