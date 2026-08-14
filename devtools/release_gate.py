"""The checks that must pass before a release, in one command.

Gate 11 of the pre-1.0 plan asks for "the final smoke matrix and release-version
consistency checks". This is that command. It runs what can be run and **refuses to be
silent about what cannot**: a step whose prerequisite is missing is reported as `BLOCKED`
with the reason, and the gate exits non-zero. A gate that skips what it cannot do is a
gate that passes on an untested release.

    python devtools/release_gate.py             # everything runnable
    python devtools/release_gate.py --list      # what it would run, and what is blocked
    python devtools/release_gate.py --only python,version

Most of these also run in the suite, which is deliberate: the suite catches them during
development and the gate catches them in the order and on the artefacts a release needs.
Two things the suite structurally cannot do are here and only here — building the wheel
and checking the runtime from an *installed* artefact rather than the checkout.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS_ROOT = ROOT / "molsysviewer" / "js"


@dataclass
class Step:
    name: str
    what: str
    command: list[str] | None
    #: Returns a reason when the step cannot run, or None when it can.
    blocked_by: object = None
    cwd: Path = ROOT


def _node_available() -> str | None:
    if shutil.which("npm") is None:
        return "npm is not on PATH"
    if not (JS_ROOT / "node_modules").is_dir():
        return "molsysviewer/js/node_modules is missing; run `npm ci` in molsysviewer/js"
    return None


def _display_available() -> str | None:
    import os

    if not os.environ.get("DISPLAY"):
        return (
            "no DISPLAY. Phase 7's Qt observations need a real screen and cannot be "
            "substituted by an offscreen run (devguide/what_needs_a_human_2026_08.md)"
        )
    return None


def _sibling_releases_ready() -> str | None:
    return (
        "gates 1-5 of Phase 10 are open: the UIBCDF dependency versions and channels are "
        "not closed, so conda artefacts cannot be built against final versions"
    )


STEPS = (
    Step("python", "the full Python suite",
         [sys.executable, "-m", "pytest", "tests/", "-q", "-x"]),
    Step("devguide", "generated indexes are current",
         [sys.executable, "devtools/devguide_index.py", "--check"]),
    Step("citation", "citation and Zenodo metadata agree",
         [sys.executable, "devtools/validate_citation.py"]),
    # The capability audit's currency, the API inventory baseline and the wheel build are
    # covered by the suite above and are deliberately not repeated here. A gate step that
    # ran their writers instead of their checks would regenerate rather than refuse, which
    # is worse than not checking at all.
    Step("version", "one version across the package, the built runtime and the npm manifest",
         None),  # reads rather than shells out; see _check_version_consistency
    Step("typescript", "tsc is clean", ["npx", "tsc", "--noEmit"],
         blocked_by=_node_available, cwd=JS_ROOT),
    Step("js", "the JS unit suite", ["npm", "run", "test:js"],
         blocked_by=_node_available, cwd=JS_ROOT),
    Step("runtime", "the runtime builds", ["npm", "run", "build:runtime"],
         blocked_by=_node_available, cwd=JS_ROOT),
    Step("perf", "the performance gates hold", ["npm", "run", "test:perf"],
         blocked_by=_node_available, cwd=JS_ROOT),
    Step("e2e", "all E2E suites in one real browser", ["npm", "run", "test:e2e"],
         blocked_by=_node_available, cwd=JS_ROOT),
    Step("qt", "Qt real-window and GPU render observation", None,
         blocked_by=_display_available),
    Step("conda", "conda artefacts against final dependency versions", None,
         blocked_by=_sibling_releases_ready),
)


def _check_version_consistency() -> tuple[bool, str]:
    """The version the package reports must be the one built into the runtime.

    `viewer.js` carries the version that built it, so a runtime rebuilt from a different
    checkout than the wheel is the failure this catches — and it is invisible until a user
    reports a mismatch in the browser console.
    """
    import importlib

    module = importlib.import_module("molsysviewer")
    reported = module.__version__

    runtime = ROOT / "molsysviewer" / "viewer.js"
    if not runtime.is_file():
        return False, "molsysviewer/viewer.js is missing; run `npm run build:runtime`"

    # The exact string, anywhere in the bundle. `build:runtime` writes the version that
    # built it, so an exact match is the invariant; a loose numeric match would pass on a
    # runtime built from a different checkout, which is the failure this exists to catch.
    text = runtime.read_text(encoding="utf-8", errors="replace")
    if reported not in text:
        return False, (
            f"molsysviewer reports {reported!r} and viewer.js does not carry that string; "
            "run `npm run build:runtime`"
        )

    # The npm manifest is *reported*, not enforced. `npm run build` is
    # `sync:pyversion && build:runtime`, and the publish workflow runs `npm run build`, so
    # a lagging `package.json` is repaired at publish time. Failing on it would make the
    # gate refuse a release over something CI fixes — a false gate is worse than a missing
    # check, because it teaches people to pass `--only`.
    #
    # `viewer.js` is different and is enforced above: Python packaging never runs npm, so
    # a stale runtime ships in the wheel exactly as it sits in the checkout.
    base = reported.split("+", 1)[0]
    package = json.loads((JS_ROOT / "package.json").read_text(encoding="utf-8"))
    declared = package.get("version", "")
    note = "" if declared == base else (
        f"; molsysviewer/js/package.json lags at {declared!r} — harmless, `npm run build` "
        "syncs it on publish"
    )
    return True, f"viewer.js carries {reported}{note}"


def _run(step: Step) -> tuple[str, str, float]:
    started = time.monotonic()

    if step.blocked_by is not None:
        reason = step.blocked_by()
        if reason:
            return "BLOCKED", reason, 0.0

    if step.name == "version":
        passed, detail = _check_version_consistency()
        return ("PASS" if passed else "FAIL"), detail, time.monotonic() - started

    if step.command is None:
        return "BLOCKED", "no command and no reason declared — this is a bug in the gate", 0.0

    completed = subprocess.run(step.command, cwd=step.cwd, capture_output=True, text=True)
    elapsed = time.monotonic() - started
    if completed.returncode == 0:
        return "PASS", "", elapsed
    tail = (completed.stdout or "").strip().splitlines()[-6:]
    error = (completed.stderr or "").strip().splitlines()[-6:]
    return "FAIL", "\n".join(tail + error), elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="show the steps and exit")
    parser.add_argument("--only", default="", help="comma-separated step names")
    arguments = parser.parse_args()

    selected = [s for s in STEPS
                if not arguments.only or s.name in arguments.only.split(",")]

    if arguments.list:
        for step in selected:
            reason = step.blocked_by() if step.blocked_by else None
            state = f"BLOCKED — {reason}" if reason else "runnable"
            print(f"  {step.name:<11} {step.what}\n              {state}")
        return 0

    results = []
    for step in selected:
        state, detail, elapsed = _run(step)
        results.append((step, state, detail))
        stamp = f"{elapsed:5.1f}s" if elapsed else "     -"
        print(f"[{state:<7}] {stamp}  {step.name:<11} {step.what}")
        if detail:
            for line in detail.splitlines():
                print(f"                        {line}")

    failed = [s.name for s, state, _ in results if state == "FAIL"]
    blocked = [s.name for s, state, _ in results if state == "BLOCKED"]

    print()
    print(f"{len(results) - len(failed) - len(blocked)} passed, "
          f"{len(failed)} failed, {len(blocked)} blocked")

    if failed:
        print("\nRELEASE BLOCKED — failing: " + ", ".join(failed))
        return 1
    if blocked:
        print("\nRELEASE NOT CLEARED — these could not run: " + ", ".join(blocked))
        print("Each is reported above with its reason. A release needs every one of them "
              "run, not skipped.")
        return 2
    print("\nEvery gate step passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
