"""Measure embedded-host responsiveness during a large popup transfer."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from molsysmt.form.string_pdb_text.to_molsysmt_MolSys import (
    to_molsysmt_MolSys as pdb_text_to_molsys,
)

from molsysviewer import MolSysView
from devtools.benchmarks.representative_scale_gate import (
    CASE_SPECS,
    build_representative_molsys,
)


ATOM_NAMES = ("N", "CA", "C", "O", "CB", "CG", "CD", "CE", "NZ", "H")
LOCAL_OFFSETS = (
    (0.00, 0.00, 0.00),
    (1.45, 0.00, 0.00),
    (2.15, 1.25, 0.00),
    (3.35, 1.25, 0.00),
    (1.45, -0.75, 1.20),
    (2.75, -1.20, 1.40),
    (3.85, -0.35, 1.10),
    (5.10, -0.65, 1.25),
    (6.15, 0.20, 1.10),
    (-0.55, -0.65, 0.00),
)


def make_pdb(atom_count: int) -> str:
    if atom_count <= 0 or atom_count > 99_999:
        raise ValueError("atom_count must be between 1 and the PDB serial limit")
    lines: list[str] = []
    for atom in range(atom_count):
        serial = atom + 1
        residue_index = atom // len(ATOM_NAMES)
        residue = residue_index + 1
        name = ATOM_NAMES[atom % len(ATOM_NAMES)]
        dx, dy, dz = LOCAL_OFFSETS[atom % len(LOCAL_OFFSETS)]
        base_x = (residue_index % 100) * 8.0
        base_y = ((residue_index // 100) % 100) * 8.0
        base_z = (residue_index // 10_000) * 8.0
        element = "H" if name == "H" else name[0]
        lines.append(
            f"ATOM  {serial:5d} {name:>4s} ALA A{residue:4d}    "
            f"{base_x + dx:8.3f}{base_y + dy:8.3f}{base_z + dz:8.3f}"
            f"  1.00 20.00          {element:>2s}"
        )
    lines.append("END")
    return "\n".join(lines)


def run(atom_count: int, threshold_ms: float, representative_case: str | None = None) -> dict[str, object]:
    # The fixture generator knows its source form. Generic form detection is
    # unrelated to endpoint isolation and dominates this benchmark for a large
    # in-memory PDB string.
    if representative_case is None:
        molsys = pdb_text_to_molsys(make_pdb(atom_count), skip_digestion=True)
        fixture = "synthetic-pdb"
    else:
        molsys = build_representative_molsys(representative_case, 1)
        atom_count = int(molsys.get_n_atoms())
        fixture = representative_case
    view = MolSysView()
    try:
        view.load(molsys)
        view._ready = True  # noqa: SLF001
        view._frontend_capabilities = {  # noqa: SLF001
            "binary_structure_data": [1],
            "max_buffer_bytes": 16 * 1024 * 1024,
        }
        sent: list[dict] = []
        view.widget.send = lambda message, buffers=None: sent.append(message)  # type: ignore[assignment]

        endpoint_id = "canvas-popup-benchmark"
        started = view._try_send_array_native_molsys(  # noqa: SLF001
            view._current_molecular_projection,  # noqa: SLF001
            target_endpoint_id=endpoint_id,
        )
        if not started:
            raise RuntimeError("array-native popup transfer did not start")

        marker = {"op": "set_region_summaries", "summaries": []}
        before = time.perf_counter()
        view._send_widget_message(marker)  # noqa: SLF001
        host_latency_ms = (time.perf_counter() - before) * 1000.0
        host_delivered = marker in sent
        popup_still_pending = bool(
            view._structure_transfer_manager(endpoint_id).has_active  # noqa: SLF001
        )
        if not host_delivered:
            raise AssertionError("embedded-host projection was blocked by popup bootstrap")
        if not popup_still_pending:
            raise AssertionError("benchmark did not measure during an active popup transfer")
        if host_latency_ms >= threshold_ms:
            raise AssertionError(
                f"host latency {host_latency_ms:.3f}ms exceeded {threshold_ms:.1f}ms"
            )
        return {
            "atoms": atom_count,
            "fixture": fixture,
            "host_latency_ms": round(host_latency_ms, 4),
            "threshold_ms": threshold_ms,
            "popup_transfer_pending": popup_still_pending,
            "host_projection_delivered": host_delivered,
        }
    finally:
        view.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--atoms", type=int, default=95_000)
    parser.add_argument("--representative-case", choices=sorted(CASE_SPECS))
    parser.add_argument("--threshold-ms", type=float, default=100.0)
    args = parser.parse_args()
    print(json.dumps(run(args.atoms, args.threshold_ms, args.representative_case), sort_keys=True))


if __name__ == "__main__":
    main()
