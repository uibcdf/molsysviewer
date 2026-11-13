---
summary: Builds silently resolve Mol* from a stale source checkout.
issue: uibcdf/molsysviewer#370
status: resolved
opened: 2026-11-12
closed: 2026-11-12
severity: high
verification: reproduced
area: [build, dependencies, reproducibility]
guard: tests/test_js_build_version_resolution.py::test_build_routes_keep_installed_molstar_when_a_source_checkout_exists
normative:
blocked_by: []
supersedes: []
---

# Implicit Mol* source override

**Resolved in source; the three-route regression passes.** #369's controlled receiving `670`
uses the real runtime/unit/harness builders with the exact project tsconfig.
Without the legacy sibling source tree all three select installed 5.4.1 and
apply the qualified component-cache repair. With a deliberate source-origin
fault at `../src_molstar/src/mol-model-formats/structure/basic/properties.ts`,
all three exit successfully with that source instead; the repair is absent.
The dependency and version metadata remain unchanged. No such tree is present
in the ordinary development checkout; the current bundle is not declared faulty.

The `compilerOptions.paths` entry in `molsysviewer/js/tsconfig.json` makes
source presence an implicit build input. The root agent instructions also
assume that obsolete inspection path. Remove the build override, keep source
inspection at the external clone and preserve the native version/byte guard.
The regression must use all three actual scripts and the real project config;
a static assertion that the JSON key disappeared would not protect resolution.

Complete duplicate inspection covers four pages, 368 issue/PR records, with
340 issues. #89 concerns version acquisition and #356/#363 own the native cache
repair; none reports this implicit source override. The original `670` outputs
and source hashes remain preserved. This fix does not update Mol* or establish
new installed/runtime compatibility.

## Resolution

The ordinary tsconfig no longer overrides Mol* resolution. The root agent
instruction points to the external source clone for inspection and distinguishes
it from installed build inputs. No scientific/runtime source or installed
dependency changed. `671` retains all three failing regression cases before
the correction; `672` passes the complete build/version module, 13 tests.
The named guard executes each actual builder with the exact project config,
an installed native package and a deliberately identifiable stale source module.
It rejects the alternate origin and checks that the reviewed cache repair
remains in the output, rather than checking a particular config spelling.

The [review receipt](../molstar_integration_review_receiving_20261112.json)
preserves the original probe, failures, final source and bounded validation.
Applicable hosted/candidate qualification remains separate; this resolution
does not update Mol*, authorize a release or close parent #369.
