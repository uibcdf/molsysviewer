import molsysviewer as msv
import molsysmt as msm

view = msv.demo["181L"]
trimmed = msm.remove(view.molsys, selection='molecule_type=="water"', to_form="molsysmt.MolSys")
view.load(trimmed, mode="replace")
view.show()
view.export.html("../_static/views/demo_181L_no_water.html", title="181L", shared_runtime="../_static", background="transparent")
