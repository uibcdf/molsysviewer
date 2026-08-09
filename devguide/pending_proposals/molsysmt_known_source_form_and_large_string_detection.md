# Known source forms and bounded detection of large molecular strings

**Status:** proposed for upstream discussion with MolSysMT

**Owner:** MolSysMT (`get_form()` and `convert()`); MolSysViewer is the motivating consumer

**Scope:** performance and API determinism; no change to MolSysViewer's scientific model

## Problem

MolSysViewer sometimes constructs an in-memory molecular representation whose form is
already known. A concrete example is the endpoint-isolation benchmark, which generates
PDB text and then needs a `molsysmt.MolSys`.

The public conversion API currently accepts a target form but no explicit source form:

```python
msm.convert(pdb_text, to_form="molsysmt.MolSys")
```

`convert()` therefore always calls `get_form(molecular_system)` before selecting the
converter. `skip_digestion=True` does not skip this step; it only skips argument
digestion.

For a generated PDB string containing 95,000 atoms, the generic detection path spent
more than seven minutes before reaching the PDB parser in the environment where this
was observed. The traceback placed the work in:

```text
convert
  -> get_form
    -> _detect
      -> catalogue.form_of_extension
```

`form_of_extension()` currently lowercases and splits the complete string on `.` as if
it were a possible file name. Coordinate-rich PDB content contains many decimal points,
so work and temporary allocations scale with the complete scientific payload even
though that payload is not a path.

Calling the known converter directly avoids that unrelated detection cost:

```python
from molsysmt.form.string_pdb_text.to_molsysmt_MolSys import (
    to_molsysmt_MolSys as pdb_text_to_molsys,
)

molsys = pdb_text_to_molsys(pdb_text, skip_digestion=True)
```

That is suitable as a temporary benchmark implementation, but importing an internal
form converter is not an appropriate long-term integration contract.

## Why both changes are needed

This proposal has two complementary parts. Neither substitutes for the other.

### 1. Make generic string-form detection bounded and content-aware

Ordinary users should not need to know or declare a source form. `get_form()` must
remain useful and must handle large in-memory molecular strings without first treating
their full contents as a path.

This fixes the default path for all callers, including interactive and exploratory code.
It also prevents a large accidental allocation before the actual parser runs.

### 2. Let an informed caller declare the source form

Infrastructure such as MolSysViewer often knows the source form by construction. It
should be able to request a deterministic conversion without paying for heuristic
detection and without importing MolSysMT internals.

An explicit source form is also useful for:

- generated molecular text;
- protocol boundaries whose schema already names the representation;
- benchmarks that must isolate conversion from detection;
- repeated conversion of homogeneous inputs;
- diagnosing detection separately from parsing.

Improving detection makes the general path fast. An explicit source form makes the
expert path deterministic.

## Proposed design

### A. Bounded detection for strings

Refine `get_form()` so that it distinguishes likely content from likely path or compact
identifier before extension lookup.

A suitable implementation should satisfy these properties:

1. A string containing line breaks is treated as content before any file-extension
   lookup.
2. Extension matching examines only a bounded filename suffix, not a `split()` of the
   complete input.
3. Compact values such as PDB identifiers and ordinary file paths retain their current
   behavior.
4. The relevant form plugin remains the authority that confirms a candidate with
   `is_form()`; the preliminary classification only chooses which detector to ask first.
5. Runtime and temporary memory before invoking the selected content detector do not
   scale with every decimal point or line in the molecular payload.

The exact content/path heuristic belongs to MolSysMT. A minimal safe direction is:

```python
if isinstance(item, str) and contains_content_marker(item):
    return sweep_string_content_forms(item)

candidate = bounded_extension_candidate(item)
...
```

`contains_content_marker()` should inspect bounded evidence where possible. It must not
copy or tokenize the complete string merely to decide whether the string is content.

### B. Public source-form hint in `convert()`

Add an explicit optional source-form argument, preferably keyword-only in spirit to
avoid disturbing the established positional API:

```python
msm.convert(
    pdb_text,
    from_form="string:pdb_text",
    to_form="molsysmt.MolSys",
)
```

Required semantics:

- `from_form=None` preserves current autodetection behavior.
- A supplied form is canonicalized and checked against MolSysMT's form catalogue.
- The selected form's own `is_form()` may validate that the input is compatible, but
  MolSysMT must not run the global detector sweep or path-extension heuristic.
- An incompatible declared form fails observably; it must not silently fall back to a
  different detected form.
- Multiple-input conversions either accept one source form per input or reject that use
  explicitly until its semantics are designed. A scalar hint must not be ambiguously
  applied to a heterogeneous list.
- `skip_digestion=True` remains independent: it does not mean "trust this source form"
  and should not acquire that hidden meaning.

Because `convert()` currently accepts `**kwargs`, MolSysMT must also ensure that
`from_form` is consumed by `convert()` itself and is never accidentally forwarded to a
form converter.

## MolSysViewer integration

After an upstream public API is available, MolSysViewer should replace the direct
internal import in `devtools/benchmarks/endpoint_isolation.py` with:

```python
msm.convert(
    pdb_text,
    from_form="string:pdb_text",
    to_form="molsysmt.MolSys",
    skip_digestion=True,
)
```

Production MolSysViewer call sites should provide `from_form` only where the form is
guaranteed by construction or by a validated protocol field. User-provided arbitrary
objects should continue through normal MolSysMT detection.

This proposal does **not** change `view.molsys` or create a new MolSysViewer
serialization format. It concerns only how a known input representation is
identified before an existing MolSysMT conversion.

## Verification

MolSysMT should add the following regression coverage:

1. A large generated PDB string is recognized as `string:pdb_text` without invoking
   file-extension detection on the full payload.
2. Extension detection has bounded auxiliary work for a large content string containing
   many dots.
3. `convert(..., from_form="string:pdb_text")` reaches the expected converter without
   calling global `get_form()`.
4. An incorrect explicit source form raises a diagnostic error.
5. Existing PDB IDs, file paths, compressed extensions, and short molecular strings keep
   their current classifications.
6. Multiple-input behavior is tested for both homogeneous and heterogeneous forms.

The performance test should report detection and parsing separately. It should use at
least a small fixture and a protein-scale text fixture, and should establish its timing
noise before choosing a threshold. The structural assertion that extension logic does
not consume the complete content is more durable than a machine-specific timing alone.

## Mutation checks

The guards should be verified by mutation:

- Remove the content-before-extension branch: the large-PDB regression must fail.
- Ignore `from_form` and call `get_form()` anyway: the explicit-source test must fail.
- Allow a false source declaration to fall back silently: the incompatibility test must
  fail.

## Adoption sequence

1. Open the corresponding proposal or issue in MolSysMT and agree on the public argument
   name and multiple-input semantics.
2. Implement bounded/content-aware detection independently of the new argument.
3. Implement and document the explicit source-form path.
4. Benchmark both detection and conversion with large in-memory molecular text.
5. Release the MolSysMT change.
6. Replace MolSysViewer's temporary direct converter import with the public API.

Until step 5, MolSysViewer's benchmark may keep the direct converter import so that it
measures endpoint isolation rather than an unrelated upstream detection bottleneck. It
must remain confined to development tooling and must not become a production dependency
on MolSysMT internals.
