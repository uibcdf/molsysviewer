"""Generate the two previews used by the molecular workbench tutorial."""

from pathlib import Path

import molsysmt as msm

import molsysviewer as msv


def main():
    output = Path(__file__).resolve().parents[1] / "_static" / "views"
    output.mkdir(parents=True, exist_ok=True)
    with msv.MolSysView() as view:
        view.load(
            [msm.systems["chicken villin HP35"]["1vii.pdb"], msm.systems["caffeine"]["caffeine.sdf"]],
            multiple=True,
            structure_indices=[0],
            labels=["Protein", "Caffeine"],
        )
        view.regions[view.load_blocks[1]["region_tag"]].set_representation("ball-and-stick", color="orange")
        view.export.html(
            str(output / "workbench_sources.html"),
            title="Protein and caffeine source regions",
            shared_runtime=str(output.parent),
            background="transparent",
        )
    with msv.new_view(msm.systems["pentalanine"]["traj_pentalanine.h5msm"], structure_indices=[0, 8, 3]) as view:
        view.interactions.hbonds.get_buch_hbonds(
            name="buch", structure_indices="all", distance_threshold="4 angstroms", pbc=False
        )
        hbonds = view.interactions.add("buch", tag="hbonds")
        hbonds.set_color("#34d399")
        hbonds.set_radius("0.025 nm")
        view.player.go_to_structure(1)
        view.export.html(
            str(output / "workbench_interactions.html"),
            title="Pentalanine hydrogen-bond contacts",
            shared_runtime=str(output.parent),
            background="transparent",
        )


if __name__ == "__main__":
    main()
