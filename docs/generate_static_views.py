"""
Helper script to export static MolSysViewer scenes for docs.

Run this after setting up your environment (molstar deps + molsysmt available).
It will overwrite files in docs/_static/views/.
"""

from pathlib import Path

import molsysviewer as mv


def ensure_dir(path: str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def quickstart():
    pdb_text = """\
ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
"""
    v = mv.MolSysView()
    v.show()
    v.load_pdb_string(pdb_text)
    v.add_sphere(center=(12.0, 12.0, 8.0), radius=3.0, color=0x00ff00, alpha=0.4)
    v.write_html(str(ensure_dir("docs/_static/views/quickstart.html")))


def pockets():
    v = mv.MolSysView()
    v.show()
    v.shapes.add_pocket_blob(
        centers=[(0, 0, 0), (3, 0, 0), (1.5, 2, 0)],
        radii=[2.0, 1.8, 1.2],
        iso_levels=[0.08, 0.15],
        iso_colors=[0x44CCFF, 0x003366],
        smoothing=1.0,
        tag="pocket-blob",
    )
    v.write_html(str(ensure_dir("docs/_static/views/pockets.html")))


def channels():
    v = mv.MolSysView()
    v.show()
    centers = [(0, 0, 0), (2, 0.5, 0.2), (4, 1, 0.5), (6, 1.5, 1.0)]
    radii = [1.2, 1.0, 0.9, 1.1]
    v.shapes.add_channel_tube(
        centers=centers,
        radii=radii,
        color_mode="segment",
        smoothing=0.5,
        tag="channel-demo",
    )
    v.write_html(str(ensure_dir("docs/_static/views/channels.html")))


def pharmacophore():
    v = mv.MolSysView()
    v.show()
    v.shapes.add_pharmacophore_features(
        centers=[(0, 0, 0), (3, 0, 0), (6, 0, 0)],
        kinds=["aromatic", "hydrophobic", "hbond_acceptor"],
        alphas=[0.5, 0.4, 0.6],
        tag="ph4-demo",
    )
    v.write_html(str(ensure_dir("docs/_static/views/pharmacophore.html")))


if __name__ == "__main__":
    quickstart()
    pockets()
    channels()
    pharmacophore()
    print("Static views exported to docs/_static/views/")
