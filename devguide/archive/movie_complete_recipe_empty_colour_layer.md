---
summary: Admit empty colour-layer maps from complete Python Movie recipes in TypeScript.
issue: uibcdf/molsysviewer#367
status: resolved
opened: 2026-11-12
closed: 2026-11-12
severity: medium
verification: reproduced
area: [movie, export, frontend]
guard: tests/test_movie_web.py::test_native_offline_movie_presentation
normative:
blocked_by: []
supersedes: []
---

# Complete Movie recipes and empty colour layers

The actual offline #320 receiving reproduces a Python/TypeScript mismatch:
`view.movie.to_dict()` retains `whole.color_layer={}` in its complete baseline.
Python accepts this empty map, but TypeScript's appearance validator used object
truthiness and rejected the uniform-colour track. The reduced preview projection
omits this field and did not expose the problem.

`movie-web-619-native` retains the original initialization timeout;
`movie-web-620-diagnostic` retains the actual exception and its full stack.
The four-page inventory contains 365 issue/PR records and 337 issues; no equivalent
report was found. Both runs used the unchanged source inputs recorded in their
private invocations. They are failures, not portable playback qualification.

The proposed correction distinguishes empty maps from maps containing per-atom
data. The canonical JS unit lane checks both directions. Closure additionally
requires `tests/test_movie_web.py::test_native_offline_movie_presentation` with
`MOLSYSVIEWER_MOVIE_BROWSER_TEST=1`: real pentalanine is exported by the public
API, Python closes, and a relocated file opens without network in real
Mol*/Chromium. Unselected skips do not qualify this boundary.

## Resolution — 2026-11-12

The TypeScript validator now checks that the colour-layer map has entries.
The canonical unit lane admits an empty map and still rejects a nonempty one.
The explicit Python guard receives the complete public-API recipe in real
offline Mol*/Chromium after Python closes: native camera, structures,
materials, labels and interaction style match independent Python samples at
forward/reversed times. File relocation, iframe, controls, final draw and
hidden layer members also pass. The first observer error and a too-short
physical-pause fixture are retained separately from product failures.

The [receiving receipt](../movie_web_receiving_20261112.json) owns exact source,
resource, outcome and evidence hashes. This closes the complete-recipe defect,
not #320, installed artifacts, hosted CI or postponed human acceptance.
