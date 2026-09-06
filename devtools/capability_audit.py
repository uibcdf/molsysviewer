"""The capability audit: one row per capability, and every checkable column computed.

Written so README, the documentation, the paper and a release cannot make slightly
different claims about the same capability. A table maintained by hand would drift the
week after it was written — that is the failure it exists to prevent — so only the
judgement is declared here and everything verifiable is derived from the repository.

**Declared** (below, in `CAPABILITIES`): what the capability is called, where its public
API lives, which documentation page owns it, where its authority sits, and its status.

**Derived**: how many public callables that API surface has and how many are digested,
which test files and E2E suites cover it, and the first released version that contains its
anchor module — read from git rather than remembered.

    python devtools/capability_audit.py             # the table, as Markdown
    python devtools/capability_audit.py --json      # the same as data
    python devtools/capability_audit.py --write     # regenerate devguide/capability_audit.md

`tests/test_capability_audit.py` fails when a declared path stops existing, when the
generated document falls behind, and when a status claims more than the evidence supports.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "devguide" / "capability_audit.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))


@dataclass(frozen=True)
class Capability:
    """One row. Everything here is a judgement; everything else is measured."""

    name: str
    #: Prefixes into the public API inventory, e.g. `view.regions.`.
    api: tuple[str, ...]
    #: The module whose first release dates the capability.
    anchor: str
    #: Where the behaviour is decided. Not where the code lives — where the truth lives.
    provenance: str
    #: Documentation page that owns it, relative to the repository root.
    docs: str | None
    #: Python test files, by name.
    unit: tuple[str, ...] = ()
    #: E2E suite names, without the `.e2e.ts`.
    e2e: tuple[str, ...] = ()
    status: str = "stable"
    #: A reproducible benchmark that records environment and methodology, if one exists.
    benchmark: str | None = None
    #: Set when someone has watched this on a real screen, with the date.
    human_observed: str | None = None
    #: Set when the row's honest reading needs a sentence the columns cannot hold.
    note: str | None = None
    #: Required of a `stable` capability that nothing has watched draw: why the label is
    #: deserved anyway. `uibcdf/molsysviewer#65` exists because two rows carried `stable`
    #: with no browser evidence and no statement that this was decided rather than
    #: inherited, and 1.0 is what turns an inherited claim into a published one.
    #:
    #: It is not an escape hatch. A capability that *draws* cannot answer this sentence
    #: honestly, and the guard says so: it accepts only the reason that nothing is drawn.
    stable_without_drawing: str | None = None
    aliases: tuple[str, ...] = field(default_factory=tuple)


#: How we know a capability works. Adapted from MolSysMT's `DOCUMENT_POLICY.md` evidence
#: labels, which qualify a *feature* rather than a report — a different axis from the
#: `verification` field in `devguide/reporting_protocol.md`, which qualifies a report.
#:
#: Their `Parity-tested` and `Scientifically validated` are not here. Both are MolSysMT's
#: questions: comparing equivalent forms, and comparing results against an independent
#: oracle. A viewer renders what MolSysMT computes, so its equivalent question is **did
#: anyone watch it draw** — and that is the one that has caught real defects here. A
#: headless harness that draws once when idle reports everything fine; Chrome's
#: `--virtual-time-budget` fast-forwards the clock without running frames; nobody had ever
#: opened an exported page and looked at its camera until a suite did.
#:
#: The labels are independent, not a ladder. A capability may be benchmarked and never
#: browser-observed.
EVIDENCE = {
    "implemented": "the code path exists and is reachable from the public API",
    "contract-tested": "Python tests exercise the documented behaviour",
    "browser-observed": "an E2E suite drives it in a real browser and asserts what it drew",
    "benchmarked": "a reproducible benchmark records environment and methodology",
    "human-observed": "someone has watched it on a real screen",
}

#: Provenance vocabulary. The distinction the paper needs: what MolSysViewer decides,
#: what it delegates, and what it merely hosts.
PYTHON = "MolSysViewer (Python authority)"
MOLSTAR = "Mol* (rendering authority)"
BROWSER = "Frontend (mirrored to Python)"
MOLSYSMT = "MolSysMT (scientific authority)"
ADDON = "Add-on (external owner)"


CAPABILITIES: tuple[Capability, ...] = (
    Capability(
        name="Whole",
        api=("view.whole.",),
        anchor="molsysviewer/whole.py",
        provenance=PYTHON,
        docs="docs/content/user/scene_management/whole.md",
        unit=("test_whole_api.py", "test_phase12_whole_panel.py"),
        e2e=("global-reprs-across-loads",),
    ),
    Capability(
        name="Regions",
        api=("view.regions.", "view.regions[…]."),
        anchor="molsysviewer/regions.py",
        provenance=PYTHON,
        docs="docs/content/user/scene_management/regions.md",
        unit=("test_region_api_completeness.py", "test_region_recipes.py",
              "test_dynamic_regions.py", "test_color_layers.py"),
        e2e=("region-hide", "region-subpanel", "range-selection"),
        note="A region survives serialisation as the recipe that produced it, not as an "
             "index list.",
    ),
    Capability(
        name="Layers",
        api=("view.layers.",),
        anchor="molsysviewer/layers.py",
        provenance=PYTHON,
        docs="docs/content/user/scene_management/layers.md",
        unit=("test_scene_object_summaries.py", "test_scene_object_identity.py"),
        e2e=("layers-subpanel", "scene-object-identity"),
    ),
    Capability(
        name="Selections and active selection",
        api=("view.selections.", "view.active_selection."),
        anchor="molsysviewer/selections.py",
        provenance=MOLSYSMT,
        docs="docs/content/user/scene_management/selections.md",
        unit=("test_selections.py", "test_active_selection.py"),
        e2e=("selection-subpanel", "range-selection"),
        note="Selection syntax is MolSysMT's; MolSysViewer digests and forwards it.",
    ),
    Capability(
        name="Representations, styles and presets",
        api=("view.styles.", "view.whole.set_representation"),
        anchor="molsysviewer/viewer/representations.py",
        provenance=MOLSTAR,
        docs="docs/content/user/representations/types.md",
        unit=("test_styles.py", "test_documented_representation_types.py",
              "test_project_style_config.py"),
        e2e=("scene-contracts",),
        note="Type names map 1:1 to Mol* built-ins. `label`, `orientation` and `plane` "
             "are deliberately not types; see the types page.",
    ),
    Capability(
        name="Annotations",
        api=("view.annotations.",),
        anchor="molsysviewer/annotations.py",
        provenance=PYTHON,
        docs="docs/content/user/overlays/labels.md",
        unit=("test_annotations.py",),
        e2e=("annotations-interaction", "annotations-subpanel"),
    ),
    Capability(
        name="Measurements",
        api=("view.measurements.",),
        anchor="molsysviewer/measurements.py",
        provenance=PYTHON,
        docs="docs/content/user/overlays/measurements.md",
        unit=("test_measurements.py",),
        e2e=("measurements-interaction", "measures-subpanel"),
    ),
    Capability(
        name="Shapes",
        api=("view.shapes.",),
        anchor="molsysviewer/shapes/__init__.py",
        provenance=PYTHON,
        docs="docs/content/user/overlays/shapes/index.md",
        unit=("test_shape_digesters.py", "test_geometry_payloads.py",
              "test_shape_render_status.py"),
        e2e=("shapes-subpanel", "shape-trajectory"),
    ),
    Capability(
        name="Trajectories and frames",
        api=("view.player.",),
        anchor="molsysviewer/player.py",
        provenance=PYTHON,
        docs="docs/content/user/movie/playback.md",
        unit=("test_playback_digesters.py", "test_structure_stream_ordering.py"),
        e2e=("shape-trajectory", "array-native-load"),
        benchmark="performance/trajectory_transport_baseline_2026_07.md",
    ),
    Capability(
        name="Trajectory plot",
        api=("view.trajectory_plot.",),
        anchor="molsysviewer/trajectory_plot.py",
        provenance=PYTHON,
        docs="docs/content/user/overlays/trajectory_plot.md",
        unit=("test_trajectory_plot.py", "test_trajectory_plot_series.py"),
        e2e=("trajectory-plot",),
        status="experimental",
        note="Observed drawing since 2026-09-05: the card, one polyline per series with "
             "a point per frame, and the labels the caller asked for.",
    ),
    Capability(
        name="Movie",
        api=("view.movie.",),
        anchor="molsysviewer/viewer/movie.py",
        provenance=PYTHON,
        docs="docs/content/user/movie/export.md",
        unit=("test_movie.py",),
        e2e=("movie-playback",),
        status="experimental",
        note="Playback observed drawing since 2026-09-05: the camera passes through "
             "intermediate positions, lands on the last keyframe, and stops short when "
             "interrupted. Export stays out -- it depends on an external encoder and is "
             "not exercised in CI.",
    ),
    Capability(
        name="Camera",
        api=("view.camera.", "view.get_camera_snapshot", "view.set_camera_snapshot",
             "view.zoom"),
        anchor="molsysviewer/viewer/camera.py",
        provenance=BROWSER,
        # Found by writing the pages the audit said were missing: this one never was.
        # `docs=None` was recorded after looking for `user/scene/camera.md`, without
        # checking whether another page already owned the capability.
        docs="docs/content/user/viewer/camera_and_controls.ipynb",
        unit=("test_camera_snapshot_request.py", "test_zoom.py"),
        e2e=("exported-page-framing",),
        note="The snapshot is the frontend's state mirrored back, and is None on a view "
             "that never rendered. Contract S9 holds camera authority.",
    ),
    Capability(
        name="save_state / load_state",
        api=("view.save_state", "view.load_state", "view.export_state",
             "view.import_state"),
        anchor="molsysviewer/viewer/state.py",
        provenance=PYTHON,
        docs="docs/content/user/export/state.md",
        unit=("test_state_serialization.py", "test_state_v2.py", "test_state_sections.py",
              "test_state_structure_identity.py", "test_state_view_state.py",
              "test_state_focus_overlays.py"),
        stable_without_drawing="Nothing about it is rendered: it writes a JSON document and "
                               "reads one back. Its contract is version 2 refusing version 1, "
                               "and the re-resolution onto a different structure -- both "
                               "checked by contract tests, neither visible on a screen.",
        note="The scene and the vantage point it was saved from: no molecular system and no "
             "history. Records the structure it was written from, and re-resolves onto a "
             "different one rather than replaying indices that mean other atoms. Version 2 "
             "refuses version 1 rather than migrating it.",
    ),
    Capability(
        name="save_session / load_session",
        api=("view.save_session", "molsysviewer.load_session"),
        anchor="molsysviewer/session.py",
        provenance=PYTHON,
        docs="docs/content/user/export/session.md",
        unit=("test_session_bundle.py",),
        # Declared experimental on purpose rather than inheriting the default. It is
        # unreleased, nothing has watched it draw, and its size policy is an open
        # question -- which is exactly the inheritance uibcdf/molsysviewer#65 is about.
        status="experimental",
        note="A `.msv` bundle carrying the molecular system alongside the state, so it "
             "reopens with nothing loaded first. No size budget: a session is as large as "
             "its trajectory.",
    ),
    Capability(
        name="HTML export and replay",
        api=("view.export.",),
        anchor="molsysviewer/exports.py",
        provenance=PYTHON,
        docs="docs/content/user/export/index.md",
        unit=("test_write_html.py", "test_export_runtime_source.py",
              "test_exported_page_opens_from_disk.py", "test_static_export_snapshot.py"),
        e2e=("export-replay", "exported-page-framing"),
    ),
    Capability(
        name="Popup",
        api=("view.build_popup_scene_snapshot",),
        anchor="molsysviewer/viewer/popup_snapshot.py",
        provenance=PYTHON,
        docs="docs/content/developer/standalone_surfaces.md",
        unit=("test_popup_snapshot.py", "test_popup_snapshot_fidelity.py",
              "test_popup_snapshot_completeness.py", "test_transport_ownership.py"),
        e2e=("popup-channel", "endpoint-lifecycle", "panel-popup-welcome"),
        benchmark="performance/qt_payload_copies_and_endpoint_isolation_2026_08.md",
    ),
    Capability(
        name="Remote sessions",
        api=("molsysviewer.remote.",),
        anchor="molsysviewer/remote/__init__.py",
        provenance=PYTHON,
        docs="docs/content/user/remote/index.md",
        unit=("test_remote_session_service.py", "test_remote_view_channel.py",
              "test_remote_session_router.py", "test_remote_render_worker.py",
              "test_remote_protocol.py", "test_remote_cli.py"),
        e2e=("remote-client-rendering", "remote-session"),
        status="experimental",
        note="The count is four because the walk inventories instances rather than "
             "classes, and the eleven classes in `__all__` are constructed by the host "
             "rather than held by a user. The surface a user actually types is the "
             "`molsysviewer-server` console script declared in `pyproject.toml`, and its "
             "page is the row's documentation. Client-side rendering is exercised by "
             "`remote-client-rendering.e2e.ts`. Server-side rendering was first "
             "certified on spika on 2026-09-05 by `remote-session.e2e.ts`, using WebGL2 "
             "with `ANGLE (NVIDIA Corporation, NVIDIA GeForce GTX 1080/PCIe/SSE2, "
             "OpenGL ES 3.2)` (uibcdf/molsysviewer#84). This is evidence for that host, "
             "not a claim that every deployment has a working GPU path. All four "
             "callables are digested and their five argument names declared, which is "
             "what closed uibcdf/molsysviewer#83 and returned the inventory baseline to "
             "zero. The packet a validator judges is passed through untouched on "
             "purpose: a digester that raised on a hostile packet would take away the "
             "structured rejection the validator exists to produce. "
             "Experimental is the page's own word: the "
             "Python API, command-line options, transport protocol and deployment "
             "configuration may change.",
    ),
    Capability(
        name="Standalone (Qt host)",
        api=("molsysviewer.launch_standalone_qt0", "molsysviewer.create_standalone_qt0_window"),
        anchor="molsysviewer/standalone_qt/__init__.py",
        provenance=PYTHON,
        docs="docs/content/developer/standalone_surfaces.md",
        unit=("test_standalone.py", "test_qt_transport_contract.py"),
        e2e=("qt-live-reload",),
        status="experimental",
        benchmark="performance/qt_transport_baseline_2026_07.md",
        human_observed="2026-07-04 — rendering, transport, the persistent view, context "
                       "menus and camera interaction. The session also found the live "
                       "reload defect (#35), which is what a person watching is for.",
        note="Transport is pinned by contract. Since 2026-09-02 the `qt-pipeline` CI job "
             "asserts under Xvfb that the pipeline completes -- bridge ready, payload "
             "served, structure loaded through software WebGL. That is not the render "
             "being correct: nothing reads the framebuffer, and #64 is the standing proof "
             "the two differ. A real GPU and a visible window remain unobserved.",
    ),
    Capability(
        name="Add-ons",
        api=("molsysviewer.addons.", "view.addons."),
        anchor="molsysviewer/addons.py",
        provenance=ADDON,
        docs="docs/content/developer/addons.md",
        unit=("test_addons.py", "test_readme_addon_table.py"),
        e2e=("panel-popup-welcome",),
        note="MolSysViewer owns the host contract; each toolkit owns and ships its "
             "integration. Maturity is declared per add-on.",
    ),
    Capability(
        name="MolSysMT integration",
        # `view.get`, `view.select` and `view.convert` were here until 2026-09-04 and had
        # not existed since the 0.22 API simplification removed them. `view.convert`
        # matched nothing; `view.get` was worse -- prefix matching absorbed ten unrelated
        # `view.get_*` event accessors into a row whose provenance is MolSysMT's
        # (uibcdf/molsysviewer#79).
        api=("view.extract", "view.whole.get",
             "view.whole.convert", "view.regions[…].get", "view.regions[…].convert"),
        anchor="molsysviewer/viewer/molsysmt_interface.py",
        provenance=MOLSYSMT,
        docs="docs/content/user/introduction/molsysmt.md",
        unit=("test_argument_name_normalization.py", "test_support_integrations.py",
              "test_tools_basic.py"),
        e2e=("structure-data-relay",),
        note="Digestion is MolSysMT's; only the caller named in an error is ours. "
             "`contains` and `is_composed_of` were removed -- `get` answers both "
             "(`get(n_waters=True) > 0`, and the set of `molecule_type`) and `msm.*` "
             "still has them. See uibcdf/molsysviewer#71.",
    ),
    Capability(
        name="Units",
        api=("molsysviewer.config.set_default_standard_units",),
        anchor="molsysviewer/_pyunitwizard.py",
        provenance="PyUnitWizard (unit authority)",
        docs="docs/content/user/introduction/units.md",
        unit=("test_public_output_units.py", "test_boundary_digesters.py"),
        stable_without_drawing="A policy about argument values, enforced before anything "
                               "reaches the frontend. There is no pixel it could be watched "
                               "producing.",
        note="Physical magnitudes are quantities, never bare numbers.",
    ),
)


def _first_release_containing(path: str) -> str:
    """The first tag that contains the commit which added `path`.

    Read from git because a hand-written 'available since' is the column most likely to be
    wrong and least likely to be noticed. Search every retained history: this repository
    has paths whose pre-0.20 and current lineages contain distinct add commits, while the
    release tags that preserve the older lineage remain authoritative for ``Since``.
    """
    adding = subprocess.run(
        ["git", "log", "--all", "--diff-filter=A", "--format=%H", "--", path],
        cwd=ROOT, capture_output=True, text=True, check=False,
    ).stdout.split()
    if not adding:
        return "unknown"

    containing = set()
    for commit in adding:
        containing.update(subprocess.run(
            ["git", "tag", "--contains", commit],
            cwd=ROOT, capture_output=True, text=True, check=False,
        ).stdout.split())
    if not containing:
        return "unreleased"

    tags_by_date = subprocess.run(
        ["git", "tag", "--sort=creatordate"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    ).stdout.split()
    return next((tag for tag in tags_by_date if tag in containing), "unreleased")


def _api_evidence(capability: Capability, inventory: dict[str, Any]) -> tuple[int, int]:
    matching = [
        item for item in inventory["callables"]
        if any(item["path"] == prefix or item["path"].startswith(prefix)
               for prefix in capability.api)
    ]
    return len(matching), sum(1 for item in matching if item["digested"])


def _evidence(capability: Capability) -> list[str]:
    """Four of the five are already known; only two are ever declared.

    That is the point of deriving them: the audit already records which tests and which
    E2E suites cover a capability, so naming what those counts *mean* costs nothing and
    makes a missing one legible. "No browser has ever seen this draw" is a sentence; a
    zero in a column is a number someone has to interpret.
    """
    labels = ["implemented"]
    if capability.unit:
        labels.append("contract-tested")
    if capability.e2e:
        labels.append("browser-observed")
    if capability.benchmark:
        labels.append("benchmarked")
    if capability.human_observed:
        labels.append("human-observed")
    return labels


def build_audit() -> dict[str, Any]:
    from public_api_inventory import build_inventory

    inventory = build_inventory()
    rows = []
    for capability in CAPABILITIES:
        public, digested = _api_evidence(capability, inventory)
        rows.append({
            "capability": capability.name,
            "api": list(capability.api),
            "public_callables": public,
            "digested": digested,
            "provenance": capability.provenance,
            "docs": capability.docs,
            "unit_tests": list(capability.unit),
            "e2e_suites": list(capability.e2e),
            "status": capability.status,
            "evidence": _evidence(capability),
            "benchmark": capability.benchmark,
            "human_observed": capability.human_observed,
            "since": _first_release_containing(capability.anchor),
            "note": capability.note,
        })
    return {"rows": rows}


def _markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Capability audit",
        "",
        "**Generated — do not edit by hand.** Run",
        "`python devtools/capability_audit.py --write`; the judgement lives in",
        "`devtools/capability_audit.py`, everything else is read from the repository.",
        "",
        "One row per capability, so that README, the documentation, the paper and a",
        "release cannot make slightly different claims about the same thing. `Public` and",
        "`digested` count the public callables of that surface; `Since` is the first tag",
        "containing the commit that added its anchor module, read from git rather than",
        "remembered.",
        "",
        "`Provenance` answers what the paper needs: whether MolSysViewer *decides* the",
        "behaviour, delegates it, or merely hosts it.",
        "",
        "| Capability | Public API | Public | Digested | Provenance | Docs | Evidence | Status | Since |",
        "|---|---|---:|---:|---|---|---|---|---|",
    ]
    for row in audit["rows"]:
        docs = f"[page]({_relative(row['docs'])})" if row["docs"] else "—"
        # The evidence set is the column that answers "how do we know"; the test and
        # suite counts that produce it are in the JSON for anyone who wants them.
        evidence = ", ".join(label for label in row["evidence"] if label != "implemented")
        lines.append(
            f"| {row['capability']} | `{'`, `'.join(row['api'])}` | {row['public_callables']} "
            f"| {row['digested']} | {row['provenance']} | {docs} | {evidence or '—'} "
            f"| {row['status']} | {row['since']} |"
        )

    undocumented = [row["capability"] for row in audit["rows"] if not row["docs"]]
    if undocumented:
        lines += [
            "",
            "## Capabilities with no user documentation page",
            "",
            "Implemented and undocumented is a different state from experimental, so the",
            "status column does not absorb it. These have a public API and tests, and a",
            "reader has nowhere to be sent:",
            "",
        ]
        lines += [f"- {name}" for name in undocumented]

    notes = [row for row in audit["rows"] if row["note"]]
    if notes:
        lines += ["", "## What a row cannot hold", ""]
        for row in notes:
            lines.append(f"- **{row['capability']}** — {row['note']}")

    unobserved = [row["capability"] for row in audit["rows"]
                  if "browser-observed" not in row["evidence"]]
    if unobserved:
        lines += [
            "",
            "## Nothing has watched these draw",
            "",
            "No E2E suite opens these in a browser and asserts what appeared. For a viewer",
            "that is the sharpest gap there is, and it is why `browser-observed` exists as",
            "a label rather than as a number in a column:",
            "",
        ]
        lines += [f"- {name}" for name in unobserved]
        lines += [
            "",
            _experimental_sentence(audit, unobserved),
        ]

    # A capability that draws nothing can never earn `browser-observed`, and saying so
    # here is the point of `uibcdf/molsysviewer#65`: the reason was written in
    # `devtools/capability_audit.py` where a reader of this document never meets it,
    # which left the claim looking inherited rather than chosen.
    undrawable = [c for c in CAPABILITIES if c.stable_without_drawing]
    if undrawable:
        lines += [
            "",
            "## Declared `stable` without drawing anything",
            "",
            "These do not render. `browser-observed` is not a label they are missing, it is",
            "one they can never earn, and the ladder reading of these labels is what makes",
            "that look like a gap. Each says why the level is deserved anyway, so the claim",
            "is made on purpose rather than inherited:",
            "",
        ]
        for capability in undrawable:
            lines.append(f"- **{capability.name}** — {capability.stable_without_drawing}")

    lines += [
        "",
        "## Two columns, two questions",
        "",
        "**Evidence** answers *how do we know it works*. The labels are independent, not a",
        "ladder: a capability may be benchmarked and never browser-observed.",
        "",
        "**They live here and nowhere else.** Four of the five are derived from what this",
        "audit already knows, and a hand-written label elsewhere would be an assertion --",
        "the thing this table exists to replace. No devguide document describes a",
        "capability: all nineteen capability pages are in `docs/`. A devguide document",
        "without an evidence label is not making a weaker claim, it is making a different",
        "kind of claim. Decided in `uibcdf/molsysviewer#61`; the record is",
        "`devguide/archive/evidence_labels_beyond_the_capability_audit.md`.",
        "",
    ]
    lines += [f"- `{label}` — {meaning}" for label, meaning in EVIDENCE.items()]
    lines += [
        "",
        "Adapted from MolSysMT's `DOCUMENT_POLICY.md`. Their `Parity-tested` and",
        "`Scientifically validated` are not here: both are their questions — comparing",
        "equivalent forms, comparing against an independent oracle. A viewer renders what",
        "MolSysMT computes, so the equivalent question is whether anyone watched it draw.",
        "",
        "This is a different axis from `verification` in",
        "[`reporting_protocol.md`](reporting_protocol.md), which qualifies how well a",
        "*report* was checked rather than how well a *capability* is verified.",
        "",
        "**Status** answers *may I depend on it*.",
        "",
        "- `stable` — the public surface is documented, digested and covered by tests, and",
        "  changing it is a deliberate act.",
        "- `experimental` — it works and is used, and one of documentation, browser-level",
        "  coverage or environment independence is missing. The note says which.",
        "- `roadmap` — declared and not implemented. No row is in this state today; the",
        "  value exists so that a future one cannot be quietly recorded as `experimental`.",
        "",
        "A capability is not `stable` merely because it has no known defect. It is stable",
        "when someone else could depend on it and find out from us before it changed.",
        "",
    ]
    return "\n".join(lines)


def _experimental_sentence(audit: dict[str, Any], unobserved: list[str]) -> str:
    """How many of the unwatched capabilities own up to it, counted rather than typed.

    This sentence was a literal "Two of them", which was true when it was written and
    silently wrong the first time a capability was added to the list -- the same decay
    the audit exists to catch, in the audit itself.
    """
    by_name = {row["capability"]: row["status"] for row in audit["rows"]}
    experimental = [name for name in unobserved if by_name.get(name) == "experimental"]
    stable = [name for name in unobserved if by_name.get(name) == "stable"]
    words = {0: "None", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five"}
    head = f"{words.get(len(experimental), str(len(experimental)))} of them "
    head += "is" if len(experimental) == 1 else "are"
    head += " already `experimental` and say so."
    if not stable:
        return head
    quoted = [f"`{name}`" for name in stable]
    named = quoted[0] if len(quoted) == 1 else ", ".join(quoted[:-1]) + f" and {quoted[-1]}"
    return (
        f"{head} {named} {'is' if len(stable) == 1 else 'are'} `stable`, which is "
        f"defensible — {'it does not draw' if len(stable) == 1 else 'none of them draws'} "
        "anything — but it is the kind of claim that "
        "should be made on purpose rather than inherited."
    )


def _relative(path: str) -> str:
    """Link from `devguide/` to a repository path."""
    return "../" + path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write", action="store_true",
                        help="regenerate devguide/capability_audit.md")
    arguments = parser.parse_args()

    audit = build_audit()
    if arguments.json:
        print(json.dumps(audit, indent=2))
        return
    document = _markdown(audit)
    if arguments.write:
        DOCUMENT.write_text(document + "\n", encoding="utf-8")
        print(f"wrote {DOCUMENT.relative_to(ROOT)}")
        return
    print(document)


if __name__ == "__main__":
    main()
