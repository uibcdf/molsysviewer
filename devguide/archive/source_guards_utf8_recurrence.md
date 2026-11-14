---
summary: New native-source guards reintroduce platform-dependent text decoding.
issue: uibcdf/molsysviewer#169
status: resolved
opened: 2026-11-13
closed: 2026-11-14
severity: medium
verification: reproduced
area: [testing, portability, molstar]
guard: tests/test_source_text_encoding.py
normative:
blocked_by: []
supersedes: []
---

# UTF-8 source-guard recurrence — resolved

The original [2026-10-06 closure](source_guards_use_platform_encoding.md)
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

Native Windows receiving in `43553954846` on `def5f417` passes all twelve
previously failing Unicode cases plus the UTF-8 declaration guards, without
omissions or a `PYTHONUTF8` override. Exact original/current JUnit identities
are compared; all seven new ZIPs match GitHub's sizes and SHA-256. The AST
guard rejects unspecified source-read encodings in these owners. The separate
Windows documentation path-identity failure is #386, not a decoding failure.
The [recovery receipt](../source_checkpoint_recovery_20261114.json) preserves
native evidence. The overall checkpoint remains failed; full core, installed
and human acceptance are not claimed by this closure.
