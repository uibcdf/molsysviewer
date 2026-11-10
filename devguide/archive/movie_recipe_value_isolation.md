---
summary: Detach version-1 Movie keyframes and imported recipes from caller data.
issue: uibcdf/molsysviewer#355
status: resolved
opened: 2026-11-10
closed: 2026-11-10
severity: medium
verification: reproduced
area: [movie, api, reproducibility]
guard: tests/test_movie_value_isolation.py::test_movie_value_boundaries_are_detached
normative: docs/content/user/movie/timeline.md
blocked_by: []
supersedes: []
---

# Movie recipe values — resolved

The original `keyframes`, `to_dict()` and `from_dict()` shared nested camera
and visibility data. In the real bundled dialanine regression, editing the
returned or imported object moves the accepted camera from x=0 to x=123 Å
and changes visibility. All three native controls fail before the fix; the
same campaign passes the 63 unrelated host service controls.

Version 1 now copies nested values at the three boundaries. The guard mutates
actual public inspection results and the supplied recipe of an independent
View, then compares with a detached original. All three cases pass; the
affected Movie/API selection passes 67 cases with one existing unavailable
dependency-error-path skip. The file format and public signatures are
unchanged. This repairs value ownership, not the remaining #320 timeline,
playback, authoring or useful media/web export requirements.
