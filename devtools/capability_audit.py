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
    #: Set when the row's honest reading needs a sentence the columns cannot hold.
    note: str | None = None
    aliases: tuple[str, ...] = field(default_factory=tuple)


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
        api=("view.selections.", "view.active_selection.", "view.select"),
        anchor="molsysviewer/selections.py",
        provenance=MOLSYSMT,
        docs=None,  # no user page: the selection story lives in MolSysMT's documentation,
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
        docs=None,  # no user page; `overlays/index.md` does not mention measurements
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
    ),
    Capability(
        name="Trajectory plot",
        api=("view.trajectory_plot.",),
        anchor="molsysviewer/trajectory_plot.py",
        provenance=PYTHON,
        docs="docs/content/user/overlays/trajectory_plot.md",
        unit=("test_trajectory_plot.py", "test_trajectory_plot_series.py"),
        status="experimental",
        note="No E2E suite opens it in a browser.",
    ),
    Capability(
        name="Movie",
        api=("view.movie.",),
        anchor="molsysviewer/viewer/movie.py",
        provenance=PYTHON,
        docs="docs/content/user/movie/export.md",
        unit=("test_movie.py",),
        status="experimental",
        note="Export depends on an external encoder and is not exercised in CI.",
    ),
    Capability(
        name="Camera",
        api=("view.camera.", "view.get_camera_snapshot", "view.set_camera_snapshot",
             "view.zoom"),
        anchor="molsysviewer/viewer/camera.py",
        provenance=BROWSER,
        docs=None,  # no user page,
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
        docs=None,  # `export/index.md` does not mention save_state/load_state
        unit=("test_state_serialization.py", "test_state_v2.py", "test_state_sections.py"),
        note="Semantic scene state only: no molecular system, camera or history. Version 2 "
             "refuses version 1 rather than migrating it.",
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
        note="Transport is pinned by contract; the render path has no automated "
             "observation on a real GPU and visible window.",
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
        api=("view.get", "view.contains", "view.is_composed_of", "view.convert",
             "view.extract"),
        anchor="molsysviewer/viewer/molsysmt_interface.py",
        provenance=MOLSYSMT,
        docs="docs/content/user/introduction/molsysmt.md",
        unit=("test_argument_name_normalization.py", "test_support_integrations.py",
              "test_tools_basic.py"),
        e2e=("structure-data-relay",),
        note="Delegates with `skip_digestion=True`, so argument names are normalised on "
             "this side.",
    ),
    Capability(
        name="Units",
        api=("molsysviewer.config.set_default_standard_units",),
        anchor="molsysviewer/_pyunitwizard.py",
        provenance="PyUnitWizard (unit authority)",
        docs="docs/content/user/introduction/units.md",
        unit=("test_public_output_units.py", "test_boundary_digesters.py"),
        note="Physical magnitudes are quantities, never bare numbers.",
    ),
)


def _first_release_containing(path: str) -> str:
    """The first tag that contains the commit which added `path`.

    Read from git because a hand-written 'available since' is the column most likely to be
    wrong and least likely to be noticed.
    """
    adding = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "--", path],
        cwd=ROOT, capture_output=True, text=True, check=False,
    ).stdout.split()
    if not adding:
        return "unknown"
    tags = subprocess.run(
        ["git", "tag", "--contains", adding[-1], "--sort=creatordate"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    ).stdout.split()
    return tags[0] if tags else "unreleased"


def _api_evidence(capability: Capability, inventory: dict[str, Any]) -> tuple[int, int]:
    matching = [
        item for item in inventory["callables"]
        if any(item["path"] == prefix or item["path"].startswith(prefix)
               for prefix in capability.api)
    ]
    return len(matching), sum(1 for item in matching if item["digested"])


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
        "| Capability | Public API | Public | Digested | Provenance | Docs | Unit | E2E | Status | Since |",
        "|---|---|---:|---:|---|---|---:|---:|---|---|",
    ]
    for row in audit["rows"]:
        docs = f"[page]({_relative(row['docs'])})" if row["docs"] else "—"
        lines.append(
            f"| {row['capability']} | `{'`, `'.join(row['api'])}` | {row['public_callables']} "
            f"| {row['digested']} | {row['provenance']} | {docs} | {len(row['unit_tests'])} "
            f"| {len(row['e2e_suites'])} | {row['status']} | {row['since']} |"
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

    lines += [
        "",
        "## Reading the status column",
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
