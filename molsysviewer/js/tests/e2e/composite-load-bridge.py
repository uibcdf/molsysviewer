"""Public composite loading of real demos for Mol* browser qualification."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import molsysmt as msm

import molsysviewer as msv
from molsysviewer import pyunitwizard as puw


def studio_bridge(sources):
    """Keep a real Python authority alive for browser-produced JSON-line requests."""
    from molsysviewer.interactions import _to_plain

    with tempfile.TemporaryDirectory(prefix="msv-studio-load-") as directory:
        paths = []
        for index, source in enumerate(sources):
            path = Path(directory) / f"source-{index}.{'pdb' if index % 2 == 0 else 'h5msm'}"
            if index % 2 == 0:
                msm.convert(source, to_form=str(path))
            else:
                msm.h5msm.write(source, str(path))
            paths.append(str(path))
        complementary = [
            str(msm.systems["pentalanine"]["pentalanine.prmtop"]),
            str(msm.systems["pentalanine"]["pentalanine.inpcrd"]),
        ]
        trajectory = msm.extract(
            msv.demo["pentalanine"].molsys,
            selection=list(range(10)),
            structure_indices=[0, 8, 3],
            to_form="molsysmt.MolSys",
        )
        msm.set(trajectory, time=None)
        trajectory_path = Path(directory) / "trajectory.h5msm"
        msm.h5msm.write(trajectory, str(trajectory_path))
        view = msv.new_view()
        view._ready = True
        sent = []
        view.widget.send = sent.append
        print(
            json.dumps({"paths": paths, "complementary": complementary, "trajectory": str(trajectory_path)}), flush=True
        )
        for line in sys.stdin:
            event = json.loads(line)
            view._handle_frontend_event(event)
            print(
                json.dumps(
                    _to_plain(
                        {
                            "messages": list(sent),
                            "records": view.load_blocks,
                            "coordinates": None
                            if view.molsys is None
                            else puw.get_value(view.get_coordinates(), to_unit="angstrom").tolist(),
                        }
                    )
                ),
                flush=True,
            )
            sent.clear()
        view.close()


sources = []
for index in range(4):
    source = msm.copy(msv.demo["dialanine"].molsys)
    coordinates = puw.get_value(source.structures.coordinates, to_unit="nm").copy()
    coordinates[..., 0] += 3 * index
    msm.set(source, coordinates=puw.quantity(coordinates, "nm"))
    sources.append(source)

if "--studio" in sys.argv:
    studio_bridge(sources)
    sys.exit(0)

batch = msv.new_view()
batch.load(sources, multiple=True, labels=["A", "A", "C", "D"])
progressive = msv.new_view()
stages = []
for source, label in zip(sources, ["A", "A", "C", "D"]):
    progressive.load(source, label=label)
    stages.append(progressive._build_embedded_runtime_snapshot())
initial = batch._build_embedded_runtime_snapshot()
batch.regions[batch.load_blocks[1]["region_tag"]].hide()
hidden = batch._build_embedded_runtime_snapshot()
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "sources.msv"
    batch.save_session(path)
    restored = msv.load_session(path)
    reopened = restored._build_embedded_runtime_snapshot()
    extracted = restored.extract(selection=list(range(22, 44)) + list(range(66, 88)))
    subset = extracted._build_embedded_runtime_snapshot()
print(
    json.dumps(
        {
            "batch": initial,
            "progressive": stages,
            "hidden": hidden,
            "reopened": reopened,
            "extracted": subset,
            "extracted_coordinates": puw.get_value(extracted.get_coordinates(), to_unit="angstrom").tolist(),
            "records": batch.load_blocks,
            "coordinates": puw.get_value(batch.get_coordinates(), to_unit="angstrom").tolist(),
        }
    )
)
