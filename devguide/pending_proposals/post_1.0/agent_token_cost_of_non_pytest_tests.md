# Proposal: Study the token cost of non-pytest test output for agent consumers

**Status:** post-1.0 study. Not a build decision.

**Scope:** The Python side already has an answer (`pytest-receptor`, see
[`../pytest_receptor.md`](../pytest_receptor.md)). This asks whether MolSysViewer's
*other* test surfaces — the JS/TS unit tests, the Playwright E2E harnesses, and the
perf/probe scripts — spend excessive tokens when the reader is an LLM or coding
agent rather than a human, and if so what the cheapest fix is. **Measurement
first; no implementation is proposed yet.**

---

## Motivation

When a coding agent runs the test suite it reads the output and pays tokens for
every character, on every iteration of a fix loop. For pytest this was measured
and addressed with `pytest-receptor` (compact, truth-preserving output). The same
class of problem plausibly exists for the non-pytest suites, but it has not been
measured here, and the mechanics differ enough that the pytest answer does not
transfer directly.

## What we already know, so the study starts from facts

- **We own most of the output.** The E2E and perf/probe tests are not run through
  a third-party runner with a reporter API; they are bundled with esbuild and run
  as plain Node scripts (`node tests/e2e/*.e2e.js`, `node tests/perf/*.perf.js`)
  driven by our own `e2e-runner.ts` and test files. Their console output is
  therefore *ours to shape* — no external "receptor" plugin is needed for these,
  unlike pytest.
- **The unit runner is known.** `npm run test:js` bundles the tests with esbuild
  and runs Node's built-in `node --test` runner. Any compact output would use a
  Node test reporter or a repo-local wrapper, not a Vitest/Jest plugin.
- **E2E has an artifact trap.** Screenshots, traces, videos, and DOM dumps are the
  real token risk if an agent tries to read them inline. The fix is structural and
  cheap: reference artifacts by path, never emit the blob. (This is how
  pytest-receptor treats captured sections and its on-disk report.)
- **The loop matters more than the size.** E2E is run manually, not in CI, so an
  agent rarely iterates on it. The token pain is worst where an agent loops — the
  unit tests during TDD — so the biggest return may be there, not in the
  more-verbose-per-event E2E.

## The question to answer

For each surface (unit, E2E, perf/probe), measure the tokens an agent actually
ingests today:

1. a **green** run;
2. a run with **one failure**;
3. a run where **one root cause cascades** into several failing tests — the case
   where pytest-receptor earned most of its saving.

Report tokens with a real tokenizer (e.g. `cl100k_base`), not bytes, and note
where the cost concentrates. Only then decide whether a compact format is worth
building, and for which surface.

## Design principles to reuse *if* a fix is warranted

Not the code — that is Python/pytest-specific — but the principles, applied in our
own harnesses (or a unit reporter):

- **verdict first:** one line with pass/fail, counts, and exit status;
- **group by root cause:** a shared broken helper failing ten tests appears once,
  with every affected test named and a way to rerun them;
- **keep what the agent cannot reconstruct** (the assertion diff, the failing
  selector) and drop what it can (framework frames, banners, timing chatter);
- **artifacts by path, never inline;**
- **never let compaction hide a real failure** — a failed or interrupted run must
  never read as a pass.

## Scope boundaries

- **This is not part of `pytest-receptor`.** That plugin is deliberately neutral
  and Python-only. Any JS work is repo-local harness formatting or, at most, a
  separate npm package — a different language and distribution.
- **Measure before building.** For pytest there was a benchmark proving
  concentrated savings; there is no equivalent evidence here yet. Do not build on
  plausibility.
- **Survey prior art first.** As with pytest — where `pytest-agent-digest` and
  `pytest-markdown-report` already existed — the JS ecosystem has compact,
  silent, and annotation reporters for the common runners. Check before writing
  anything.

## Open items

- Fix the tokenizer and the three scenarios per surface.
- Identify whether an existing JS reporter already covers the need.

## Report anomalies upstream where relevant

If the study is run with `pytest-receptor` in the loop for the Python side and
that output is itself wrong or insufficient, that belongs upstream in the
`pytest-receptor` repository (`devguide/pending_bugs/` or `pending_proposals/`),
not here. This proposal is about the *non-pytest* surfaces only.
