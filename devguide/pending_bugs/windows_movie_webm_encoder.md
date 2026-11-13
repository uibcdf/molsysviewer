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

## Native diagnosis

The single source-only Windows diagnostic `43521107544`, on published
`26f935f0`, reproduces **one failure / 23 passes / zero skips**. Original
native stderr is `Unknown encoder 'libvpx-vp9'`. ImageIO-FFmpeg is 0.8.1;
the selected executable is FFmpeg 9.0.2 with SHA-256
`5de10060156daa8c128463cc1f8433a03f78535e7622873535a0e94d9bf2d2a7`.
Both original ZIPs match GitHub's sizes and digests. This is a concrete
codec-availability boundary, not an established Mol* rendering regression.

The inspected conda-forge recipe at
[`9820e152b533a05e4c3fc01b33a933652e6751a7`](https://github.com/conda-forge/ffmpeg-feedstock/blob/9820e152b533a05e4c3fc01b33a933652e6751a7/recipe/meta.yaml)
excludes libvpx on Windows, while declaring AOM/SVT AV1. The corresponding
build script enables libvpx only on Linux/macOS and enables libaom on all
platforms. This explains the observed absence; a recipe declaration alone
does not qualify actual AV1 encoding or browser playback.

Before changing the advertised WebM/VP9 contract, discuss an explicit codec
choice and documented automatic selection versus requiring a separately
qualified VP9-enabled FFmpeg. The maintainer's preference is requested;
no codec is silently substituted and no format assertion is removed.
