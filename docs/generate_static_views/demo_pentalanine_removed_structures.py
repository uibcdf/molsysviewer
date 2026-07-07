import molsysviewer as viewer
import molsysmt as msm

view = viewer.demo["pentalanine"]
trimmed = msm.remove(view.molsys, structure_indices=[0, 1, 2], to_form="molsysmt.MolSys")
view.load(trimmed, mode="replace")
view.show()
view.export.html("../_static/views/demo_pentalanine_removed_structures.html", title="Pentalanine", mode="lite")
