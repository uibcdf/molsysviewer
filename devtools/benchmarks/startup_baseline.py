"""What it actually costs to get a viewer on screen.

This exists because the devguide's startup numbers measured something that no
longer happens. Every "3-5 second freeze" figure in
`standalone_performance_and_depythonization.md` and
`standalone_v2_evolution_plan.md` was Numba JIT compilation, and **MolSysMT was
rewritten in Rust for 1.0 and no longer uses Numba**. Those numbers are not
merely stale, they measure an absent mechanism — and a standalone architecture
decision (Option 1 vs Option 3) rests on them.

So this measures the stages that remain, separating three things the old figure
conflated:

- **one-time cost** — lazy imports, paid once per process;
- **per-viewer cost** — what a second `MolSysView()` costs;
- **per-load cost** — what every load pays, which is the one that scales.

It deliberately reports MolSysMT's share separately. Reading a trajectory is
their work, not ours, and mixing them produced the impression that the viewer was
slow when most of the wall clock was upstream.

    python devtools/benchmarks/startup_baseline.py
    python devtools/benchmarks/startup_baseline.py --case dialanine
    python devtools/benchmarks/startup_baseline.py --repeats 5

Not covered here: Qt WebEngine initialization and browser-side decode, which
need a real window. Measure those with the Qt harness, not this one.
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

CASES = {
    "pentalanine-5000": "pentalanine",
    "dialanine": "dialanine",
}


def _ms(t0: float) -> float:
    return (time.perf_counter() - t0) * 1000.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", default="pentalanine-5000", choices=sorted(CASES))
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()

    # Stage 1 — import cost, measured before anything else touches these modules.
    t0 = time.perf_counter()
    import molsysviewer  # noqa: F401
    import_viewer_ms = _ms(t0)

    t0 = time.perf_counter()
    import molsysmt as msm
    import_molsysmt_ms = _ms(t0)

    from molsysviewer.systems import systems

    source = getattr(systems, CASES[args.case]).path

    # Stage 2 — MolSysMT's own share: reading the file into a MolSys.
    t0 = time.perf_counter()
    molsys = msm.convert(source, to_form="molsysmt.MolSys")
    convert_ms = _ms(t0)

    n_atoms = molsys.topology.n_atoms
    n_structures = molsys.structures.n_structures

    # Stage 3 — first viewer vs subsequent ones. The gap is the lazy-import
    # chain (anywidget, ipywidgets, traitlets, the runtime bundle), paid once.
    t0 = time.perf_counter()
    first_view = molsysviewer.MolSysView()
    first_view_ms = _ms(t0)
    first_view.close()

    warm_view_ms = []
    for _ in range(args.repeats):
        t0 = time.perf_counter()
        warm_view_instance = molsysviewer.MolSysView()
        warm_view_ms.append(_ms(t0))
        warm_view_instance.close()

    # Stage 4 — the load, on an already-converted object so this is *our* cost.
    # Separate registration from each negotiated delivery path. A load before
    # `ready` now records a lazy molecular projection and must not be mislabeled
    # as JSON preparation.
    register_ms = []
    binary_load_ms = []
    json_load_ms = []
    for _ in range(args.repeats):
        view = molsysviewer.MolSysView()
        view.widget.send = lambda *a, **k: None  # type: ignore[assignment]
        t0 = time.perf_counter()
        view.load(molsys)
        register_ms.append(_ms(t0))
        view.close()

        view = molsysviewer.MolSysView()
        view.widget.send = lambda *a, **k: None  # type: ignore[assignment]
        view._ready = True
        view._frontend_capabilities = {
            "binary_structure_data": [1],
            "max_buffer_bytes": 1024 * 1024 * 1024,
        }
        t0 = time.perf_counter()
        view.load(molsys)
        binary_load_ms.append(_ms(t0))
        view.close()

        view = molsysviewer.MolSysView()
        view.widget.send = lambda *a, **k: None  # type: ignore[assignment]
        view._ready = True
        t0 = time.perf_counter()
        view.load(molsys)
        json_load_ms.append(_ms(t0))
        view.close()

    warm_view = statistics.median(warm_view_ms)
    register = statistics.median(register_ms)
    binary_load = statistics.median(binary_load_ms)
    json_load = statistics.median(json_load_ms)
    ours = first_view_ms + binary_load
    theirs = import_molsysmt_ms + convert_ms

    print(f"case                  {args.case}  ({n_atoms} atoms x {n_structures} structures)")
    print(f"repeats               {args.repeats} (median reported)")
    print()
    print(f"import molsysviewer   {import_viewer_ms:9.0f} ms   one-time")
    print(f"import molsysmt       {import_molsysmt_ms:9.0f} ms   one-time, MolSysMT")
    print(f"msm.convert(file)     {convert_ms:9.0f} ms   per file, MolSysMT")
    print(f"MolSysView() first    {first_view_ms:9.0f} ms   one-time (lazy imports)")
    print(f"MolSysView() warm     {warm_view:9.0f} ms   per viewer")
    print(f"load, register lazy   {register:9.0f} ms   before frontend ready")
    print(f"load, array-native    {binary_load:9.0f} ms   normal negotiated path")
    print(f"load, direct JSON     {json_load:9.0f} ms   compatibility path")
    print()
    print(f"MolSysViewer's share  {ours:9.0f} ms")
    print(f"MolSysMT's share      {theirs:9.0f} ms")
    print(f"first canvas, total   {ours + theirs:9.0f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
