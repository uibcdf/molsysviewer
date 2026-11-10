import json
import os
import shutil
import statistics
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest
from devtools.benchmarks.representative_scale_gate import (
    CASE_SPECS,
    _current_rss_bytes,
    _peak_rss_bytes,
    build_representative_molsys,
)


def test_representative_scale_matrix_uses_intact_molecular_supercells():
    assert CASE_SPECS["small"].resource_name == "181l.bcif.gz"
    assert CASE_SPECS["medium"].resource_name == "traj_chicken_villin_HP35_solvated.h5msm"
    assert CASE_SPECS["large"].copies == 24
    assert CASE_SPECS["xlarge"].copies == 72
    for spec in CASE_SPECS.values():
        assert spec.copies == spec.grid[0] * spec.grid[1] * spec.grid[2]


def test_small_representative_fixture_preserves_atoms_and_does_not_invent_time():
    molsys = build_representative_molsys("small", 2)

    assert molsys.get_n_atoms() == 2882
    assert molsys.structures.n_structures == 2
    assert molsys.structures.box is not None
    assert molsys.structures.time is None


def test_browser_benchmark_medians_match_independent_reference():
    node = shutil.which("node")
    assert node, "The frontend benchmark guard requires the development Node installation"
    cases = [[1, 3], [4, 1, 3, 2], [9, 1, 3], [0], [-4, -1], [1e308, 1e308], [5e-324, 1e-323]]
    expected = [float(statistics.median([Fraction(value) for value in case])) for case in cases]
    code = """
import {readFileSync} from 'node:fs';
import {transformSync} from 'esbuild';
const source=readFileSync('tests/perf/summary-statistics.ts','utf8');
const code=transformSync(source,{loader:'ts',format:'esm'}).code;
const {median,medianOrNull}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const cases=JSON.parse(readFileSync(0,'utf8'));
let rejected=0;
for(const input of [[],[NaN],[Infinity],[-Infinity]]){
    try{median(input);}catch(error){if(error instanceof RangeError)rejected++;else throw error;}
}
console.log(JSON.stringify({values:cases.map(median),empty:medianOrNull([]),rejected}));
"""
    result = subprocess.run(
        [node, "--input-type=module", "-e", code],
        cwd=Path(__file__).resolve().parents[1] / "molsysviewer/js",
        env={**os.environ, "GOMAXPROCS": "1"},
        input=json.dumps(cases),
        text=True,
        capture_output=True,
        check=True,
        timeout=20,
    )
    actual = json.loads(result.stdout)
    assert actual == {"values": expected, "empty": None, "rejected": 4}
    # The four benchmark entrypoints share this tested statistic.
    perf = Path(__file__).resolve().parents[1] / "molsysviewer/js/tests/perf"
    for name in ["representative-scale", "trajectory-transport", "exclusive-ownership", "message-toll"]:
        caller = (perf / (name + ".perf.ts")).read_text()
        assert 'from "./summary-statistics.js"' in caller
        assert "function median(" not in caller


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process memory API")
def test_windows_benchmark_memory_counters_are_available():
    current = _current_rss_bytes()
    peak = _peak_rss_bytes()
    assert 0 < current <= peak
