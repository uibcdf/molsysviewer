"""Real initial TcTIM or empty widget for the first-load Welcome browser guard."""

import argparse
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import molsysviewer as msv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--empty", action="store_true")
    parser.add_argument("--pdb-id", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--invalid", action="store_true")
    args = parser.parse_args()
    if args.empty or args.invalid:
        view = msv.MolSysView()
    elif args.pdb_id:
        # Optional receiving of the reporter's exact network-backed workflow.
        view = msv.new_view("1TCD")
    else:
        # The normal CI guard uses MolSysMT's real bundled TcTIM, via new_view,
        # so acquisition of an external PDB file is not its prerequisite.
        view = msv.demo["1TCD"]
    if args.json:
        view.widget.supports_array_native_buffers = False
    if args.invalid:
        # A prepared initial reference whose fetch succeeds but JSON decoding
        # fails: exercise the real frontend failure/empty-state cleanup.
        view._send({"op": "load_molsys_payload_ref", "ref": {"url": "data:application/json,invalid"}})
    runpy.run_path(str(Path(__file__).with_name("canvas-popup-bridge.py")))["serve"](view)


if __name__ == "__main__":
    main()
