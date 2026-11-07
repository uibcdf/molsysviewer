"""Real molecular messages and literal titles for the DataCard browser guard."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from molsysviewer.loaders.json_molsys import build_json_molsys_message

import molsysviewer as msv


def fixture():
    titles = {
        "initial": 'Density <em data-literal-card="initial">α & β</em> "nm" < 0.01',
        "updated": 'Updated <b data-literal-card="updated">H-bonds & ions</b> > 0',
        "restored": 'Recovered <i data-literal-card="restored">γ & δ</i> "value"',
    }
    records = {}
    with msv.demo["pentalanine"] as full:
        with full.extract(structure_indices=[0, 8, 3]) as view:
            for name, title in titles.items():
                # These observations exercise text/plot transport, not a detector.
                view.trajectory_plot.show(
                    {"synthetic": [0.0001, 0.0002, 0.0005]},
                    title=title,
                    y_label="synthetic / nm",
                    tag="literal-card",
                )
                records[name] = view.trajectory_plot.records()[0]
            saved = json.loads(json.dumps(view.export_state()))
            with msv.new_view(view.molsys) as recovered:
                recovered.import_state(saved)
                assert recovered.trajectory_plot.records()[0] == records["restored"]
            return {
                "load": build_json_molsys_message(view.molsys, label="pentalanine-title-control"),
                "plots": records,
                "expected": {"atoms": 62, "structures": 3, "titles": titles},
            }


if __name__ == "__main__":
    Path(sys.argv[1]).write_text(json.dumps(fixture()), encoding="utf-8")
