"""Check ordinary viewing against a real published provider without Interactions.

Pass an extracted package's site-packages directory, or use --installed in an
isolated environment. No provider methods are mocked and no package is installed
or modified by this probe.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
import sysconfig
from pathlib import Path


def run(provider_path, expected_version, *, installed=False, expected_viewer_version=None):
    if not installed:
        sys.path.insert(0, str(provider_path.resolve()))
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import molsysmt as msm

    import molsysviewer as msv

    assert msm.__version__ == expected_version, msm.__version__
    if installed:
        sites = {Path(sysconfig.get_path(kind)).resolve() for kind in ("purelib", "platlib")}
        for package in (msm, msv):
            assert any(Path(package.__file__).resolve().is_relative_to(site) for site in sites), package.__file__
            assert package.__version__ == importlib.metadata.version(package.__name__), package.__name__
    else:
        assert Path(msm.__file__).is_relative_to(provider_path.resolve()), msm.__file__
    if expected_viewer_version is not None:
        assert msv.__version__ == expected_viewer_version, msv.__version__
    with msv.demo["pentalanine"] as source, msv.new_view(source.molsys, structure_indices=[0, 8, 3]) as view:
        assert view.interactions.analyses() == []
        assert view.interactions._summary_message()["backend_available"] is False
        snapshot = view._build_embedded_runtime_snapshot()
        assert any(message.get("op") == "set_interaction_summaries" for message in snapshot)
        try:
            view.interactions.hbonds.get_buch_hbonds(name="buch")
        except ValueError as error:
            assert "compatible MolSysMT" in str(error), str(error)
        else:
            raise AssertionError("Unsupported provider accepted the experimental workflow")
        print(
            json.dumps(
                {
                    "provider": msm.__version__,
                    "source": msm.__file__,
                    "viewer": msv.__version__,
                    "viewer_source": msv.__file__,
                    "installed": installed,
                    "ordinary_view": "passed",
                    "interaction_gate": "explicit",
                }
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider_path", type=Path, nargs="?")
    parser.add_argument("--expected-version", default="0.22.4")
    parser.add_argument(
        "--installed", action="store_true", help="Require both packages from this interpreter's site-packages"
    )
    parser.add_argument("--expected-viewer-version")
    args = parser.parse_args()
    if args.installed == (args.provider_path is not None):
        parser.error("Use either provider_path or --installed.")
    run(
        args.provider_path,
        args.expected_version,
        installed=args.installed,
        expected_viewer_version=args.expected_viewer_version,
    )
