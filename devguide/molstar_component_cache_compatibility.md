# Mol* component-cache compatibility

MolSysViewer's build applies a narrow lifetime repair to the private native
component-name cache. It supports only the reviewed npm Mol* 5.4.1 module
bytes, checked by version and SHA-256 in
[`molstar-component-cache.mjs`](../molsysviewer/js/scripts/molstar-component-cache.mjs).
Runtime, unit and browser-harness builds use the same adapter. Unknown
versions or changed imported source fail the build for review. Installed
`node_modules` files are never edited; the dependency version and lock remain
unchanged by this repair.

For absent/empty `chem_comp`, the original `getUniqueComponentNames` uses
`memoize1`'s unbounded strong Map keyed by BasicData. The key retains atom_site
and coordinate storage. The repair changes only that private cache to weak
object keys. It leaves generic `memoize1`, component definitions and numeric
data unchanged. It does not copy, detach or erase coordinate buffers.

Upstream already documents this as `01/B1 = 04/B1`; it is not a new discovery.
The [independent review](molstar_component_cache_report_review_20261112.json)
receives exact unmodified npm 5.4.1 and public 5.13.1 reproductions plus
current-source controls. The
[receiving record](molstar_component_cache_receiving_20261112.json) separates
working source, actual Jupyter before/after and still-pending broader gates.
The actual-host guard is
`tests/test_jupyter_live_capture.py::test_live_jupyter_controller_release`.

This is a temporary provider-compatibility adaptation owned by MolSysViewer's
maintainers under uibcdf/molsysviewer#356. Diego requested local tracking
instead of another upstream report; uibcdf/molsysviewer#363 owns monitoring
and eventual removal. No upstream issue/PR is published or authorized.
Review by **2026-12-12**, or earlier at the next dependency/release checkpoint.
The removal condition is a published native replacement received against the
same lifetime and independent-view controls, with applicable combined gates.
The broader upgrade remains separately scoped under
uibcdf/molsysviewer#115. Neither this exception nor the small passing guard
certifies the full prolonged campaign, installed artifacts or a release.
