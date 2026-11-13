---
summary: Native Windows WebM encoding fails without retained encoder stderr.
issue: uibcdf/molsysviewer#385
status: active
opened: 2026-11-13
closed:
severity: medium
verification: reproduced
area: [movie, export, portability]
guard:
normative:
blocked_by: []
supersedes: []
---

# Windows WebM receiving

Exact-source run `43513962722` fails the real four-frame WebM control on
Windows/Python 3.14. Linux/macOS pass the same encode/decode assertion and
Windows passes MP4. The encoder exits nonzero at finish. Neither the generic
RuntimeError nor the original JUnit records native stderr. The four original
artifact ZIPs are downloaded and independently match GitHub's sizes and
SHA-256; none includes the encoder log. The cause remains unknown.

Keep the format, original deadlines, four independently decoded samples,
colour tolerance and frame-rate/duration assertions. The test now attaches
bounded native stderr and executable/version identity to the original
exception. A manual, source-only Windows encoder diagnostic selects the
unchanged encoder module and preserves its own logs. It cannot qualify the
full source matrix, any installed package or Mol* itself. Diagnose the native
failure before changing codec parameters or repeating the complete matrix.

Parent boundaries are #372 (source qualification) and #320 (Movie readiness).
The all-state duplicate review acquired all four pages / 355 non-PR issues;
no equivalent focused failure was found. Original native outcomes remain
failed even if later receiving succeeds.
