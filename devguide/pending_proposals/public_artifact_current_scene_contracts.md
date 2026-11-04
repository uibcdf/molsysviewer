---
summary: Deliver a public artifact covering current scene handles and frame notifications.
issue: uibcdf/molsysviewer#294
status: partial
opened: 2026-11-04
closed:
verification: upstream
area: [packaging, addons, compatibility]
guard:
normative:
blocked_by: []
supersedes: []
---

# Public artifact for current scene contracts

## What and how

DockingMT reports missing handle `info()` and Python-navigation callbacks in
public Viewer 0.24.0 build 1, despite source delivery under #217/#291. Its
[committed receiving](https://github.com/uibcdf/dockingmt/blob/2d7b410e3a8bf74a833554a4f55a01defd65f0e2/devguide/validation/public_viewer_receiving.md)
also reports an initialization failure with private DockingMT, controlled
MolSysMT `de7ffad2a`, pandas 3.0.6 and its recorded support providers. The error
does not establish a standalone pandas/NumPy defect or an import-order workaround.

Independent local receiving confirms both API gaps in the original public
Viewer build-1 payload, using public MolSysMT and pandas 2.3.3. This verifies
those two observations outside DockingMT; it does not reproduce its separate
initialization failure or its full controlled dependency composition.

Current-source probes receive both scene contracts with public MolSysMT/pandas
2.3.3 and corrected MolSysMT source/pandas 3.1.0. They do not include that exact
private composition. Public-provider strict CI has the separately identified
native #431 boundary. This report owns the temporary consumer CI selection;
its review date and removal trigger are in
[the operational record](../public_provider_ci_compatibility_20261104.md).
MolSysMT owns repaired scientific-package delivery.

## Why and acceptance

Prepare an additive pre-1.0 artifact covering the delivered contracts after the
maintainer accepts its scope. 0.25.0 remains unfrozen. Complete source gates,
bind exact producer/file hashes and qualify the declared installed pair and
platforms before separately authorized publication. Preserve all public 0.24.0
files, tags, hashes and their original qualification.

Keep the initialization subcase open until its actual composition is reproduced
or downstream receiving establishes its disposition on the covering artifact.
DockingMT owns repeating its bounded installed checks; GUI/browser/scientific
acceptance remain separate. Every addon function need not finish first.
No candidate, artifact or publication is authorized by this record.
