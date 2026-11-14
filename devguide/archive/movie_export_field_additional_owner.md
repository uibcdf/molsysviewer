---
summary: The native Movie Studio receiver retains the old exact output label.
issue: uibcdf/molsysviewer#383
status: resolved
opened: 2026-11-13
closed: 2026-11-13
severity: low
verification: inspected
area: [testing, movie, browser]
guard: tests/test_movie_studio.py::test_live_movie_export_field_matches_studio
normative:
blocked_by: []
supersedes: []
---

# Additional Movie Studio receiving owner — resolved

The [original actual-Jupyter correction](jupyter_movie_export_field_label.md)
retains its complete eight-case notebook evidence. A subsequent source audit
finds the same stale exact output label in the distinct native-browser owner
`movie-studio.e2e.ts`. The expanded guard now derives the actual Studio label
and requires both owners to match it, allowing their normal quote/spacing
styles. The native selector is corrected without changing the label or
operation deadlines. Complete native Studio receiving `789` passes the existing
authoring, popup, seek/preview/pause and export scenario, plus the new explicit
AV1 branch. Its native exit is zero, all selected inputs remain unchanged and
cleanup has no survivors/errors or resource stop. The named guard checks both
actual receiver owners against the current panel field; reverting either
selector fails it. The [codec receipt](../movie_codec_receiving_20261113.json)
retains original failed attempts and their distinct causes. Earlier eight-case
actual-Jupyter receiving stays within its own source scope. This closure does
not qualify Windows, installed packages or the complete Movie feature.
