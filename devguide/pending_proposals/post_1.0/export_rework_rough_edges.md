# Rough edges of the 2026-08 export rework, to review cold

**Status:** post-1.0 review. Nothing here is broken and nothing here blocks
anybody. These are the four places where the export rework of 2026-08-04 chose an
answer that works but does not feel right, written down while the reasons were
fresh so that a later reader can look for a better one without re-deriving the
problem.

**Origin:** asked for on 2026-08-04, at the end of the work recorded in
[`../embedding_views_in_external_documentation.md`](../embedding_views_in_external_documentation.md)
§8. The judgement then was: good work overall, with one piece that should be
removed if nobody uses it, one test that does not run where it should, one small
wart, and one smell that predates all of it.

**How to review this.** Do not treat any item as a defect report. For each, the
useful question is *"knowing what we know now, is there an answer that removes
the trade-off rather than accepting it?"* If there is not, say so in the file and
close the item — an accepted trade-off that has been re-examined once is worth
more than an open question nobody revisits.

---

## 1. A molecular viewer that ships an HTTP server

`molsysviewer.tools.preview` and `python -m molsysviewer.preview` exist because a
view that shares a runtime must be served, and an author has no server between
building their site and publishing it.

**Why it grates.** Serving files is not this library's job. It is scope that
arrived as a workaround for a browser policy, and the argument-digestion
convention makes a 90-line tool cost five files: the tool, the CLI module, and
digesters for `port`, `open_browser` and `serve_forever` that exist only for it.

**What was considered and rejected at the time.** Telling authors to run
`python -m http.server` (free, but the failure it prevents is exactly the one
authors do not know they have); a Sphinx-only solution (leaves everyone else
out); making the shared shape openable from disk, which is
[`../classic_script_runtime_for_offline_bundles.md`](../classic_script_runtime_for_offline_bundles.md).

**The decision rule proposed then:** if nobody has used it after six months,
delete it without ceremony. Check first whether the user page and the
troubleshooting page still point at it, since removing it means rewriting the
answer to "why is my embed blank?".

**A better answer might be:** the classic-script runtime landing for other
reasons, which would make `preview` a convenience rather than the only way to see
your own work — at which point deleting it costs nothing.

## 2. The test that proves the headline property does not run in CI

`tests/test_exported_page_opens_from_disk.py` opens an exported file in a real
Chromium and asserts that it boots. It is the only check of the property the
whole rework exists for, and it **skips when no browser is on the PATH**.

**Why it grates.** `engineering_rules.md` §4 refuses silent skips. This one is
not silent — it names its reason — but the effect is close enough: a CI without a
browser goes green having verified nothing about the property that matters most.

**Options, none costed yet:**

- install Chromium in the CI image and let the test run everywhere. Cheapest to
  reason about, and it makes the suite depend on a browser;
- run it only in a dedicated job, next to
  [`qt_render_check_on_a_gpu_runner.md`](qt_render_check_on_a_gpu_runner.md) —
  the same problem for the same reason, and the same self-hosted machine could
  answer both;
- accept it and mark it explicitly as an environment-gated check, with the gate
  recorded where the release checklist can see it.

The middle option is the one that looks right today, precisely because the Qt
render check already needs that machine. **Review these two together, not
separately.**

## 3. A page that reaches the network without the reader asking

An export from a **released** version carries the pinned CDN URL as a last-resort
candidate. It is only reached when the local copy fails, which today means only
when the page was opened from a disk.

**Why it grates.** It is the one part of the design that does something the
author did not see when they published. Pinned exact, so reproducibility holds —
the same runtime by another road — but "this page may contact jsDelivr" is not
written on the page, and a reader on an air-gapped machine gets a failed request
they did not expect.

**Possible better answers:** make it opt-in (`shared_runtime="docs/_static"` vs
something explicit), which costs an argument we just finished collapsing into
one; or make the page *say* it, which is really
[`../exported_page_self_declaration.md`](../exported_page_self_declaration.md)
wearing another hat; or drop the tail entirely if the classic-script route lands,
since then the local copy answers from disk too.

**Do not resolve this before item 1 and
[`../classic_script_runtime_for_offline_bundles.md`](../classic_script_runtime_for_offline_bundles.md).**
All three collapse together if that one is ever done.

## 4. JavaScript inside a Python f-string

`_build_lite_html` is a Python f-string containing the page's boot script, which
now has two paths (embedded blob first, then candidates) and doubled braces
throughout. It predates this rework; the rework made it longer.

**Why it grates.** It is the only JavaScript in the project that is not in
`js/src/`, not type-checked, not covered by `test:js`, and only testable by
opening a browser — which is exactly why item 2 exists. Every rule in
`engineering_rules.md` §3 about generated artefacts points away from writing code
this way.

**What it would take.** Move the boot script into `js/src/` as a small entry
point, build it alongside the runtime, and have Python emit only data — the
scene, the UI config, the candidates, the embedded runtime. Python would compose,
not write code. That is a contained change with one real question attached: the
boot script is what loads the runtime, so it cannot itself come from the runtime
bundle, and it would need to be a second, tiny artefact.

**Why not now.** It is a refactor with no user-visible effect, landed on top of a
rework that just changed the same function.

---

## What this episode said about where the blind spots are

Worth keeping, because it is not a code item and will otherwise be forgotten.

Both real defects found on 2026-08-04 were found **by questions, not by tests**:

- `embed_iframe` raised on its own default `width="100%"`, because `width` is a
  physical length everywhere else in the library. The suite was green: all four
  tests passed `skip_digestion=True` and never crossed the argument layer, and
  every example in the user page is a markdown cell that Sphinx does not execute.
- The export called self-contained fetched `require.js` and two
  `@jupyter-widgets` bundles at open time. Nothing in the repository says so; it
  took opening the file in a browser with the network disabled.

The pattern in both: **the repository was consistent with itself and wrong about
the product.** Tests asserted what the code does, documentation described what we
meant, and neither of them opened the artifact a user would receive. This is the
same finding as
[`../first_read_comprehension_gaps_2026_08.md`](../first_read_comprehension_gaps_2026_08.md)
from the other side — that one was about a reader misunderstanding the
repository, this one is about the repository misunderstanding its own output.

The cheap countermeasure already exists and should be extended rather than
admired: every claim a user-facing page makes about *what an artifact does* wants
a test that produces the artifact and checks it. `test_exported_page_opens_from_disk.py`
and `test_docs_static_views.py` are the two that do this today. Candidates for
the same treatment: the notebook widget's boot path, and the popout — the two
places where nobody has yet checked with a real browser.
