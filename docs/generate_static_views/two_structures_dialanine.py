import molsysviewer as viewer
import molsysmt as msm

view = viewer.demo["dialanine"]
second_structure = msm.copy(view.molsys)
msm.structure.translate(second_structure, "[0.2, 0.0, 0.0] nm", in_place=True)
view.append_structures(second_structure)
view.show()
view.write_html("../_static/views/two_structures_dialanine.html", title="Dialanine (2 structures)", mode="lite")
