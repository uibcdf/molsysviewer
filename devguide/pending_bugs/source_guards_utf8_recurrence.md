---
summary: New native-source guards reintroduce platform-dependent text decoding.
issue: uibcdf/molsysviewer#169
status: active
opened: 2026-11-13
closed:
severity: medium
verification: reproduced
area: [testing, portability, molstar]
guard:
normative:
blocked_by: []
supersedes: []
---

# UTF-8 source-guard recurrence

The original [2026-10-06 closure](../archive/source_guards_use_platform_encoding.md)
retains its successful three-platform evidence. The issue is reopened for new
reads introduced during #372, not because that historical execution failed.

Source checkpoint `43513962722` on `6e13bd26` fails the UTF-8 declaration guard
in all three hosts. Windows additionally fails twelve native-source checks:
`test_js_build_version_resolution.py` and `test_molstar_compatibility.py`
attempt to decode Mol* UTF-8 sources with cp1252. The copied native source
contains an undefined cp1252 byte. No renderer or molecular result is involved.

The correction declares UTF-8 on source/fixture reads and writes in those
modules, `test_reporting_protocol.py` and `test_js_source_coverage.py`, then
extends the existing AST declaration guard to cover the added owners. There
is no PYTHONUTF8 workaround, changed Unicode source or removed assertion.
Focused local receiving and native Windows requalification are separate;
retain the original failed JUnit and its byte-verified artifact.
