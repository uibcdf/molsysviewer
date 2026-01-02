import molsysviewer as viewer
import molsysmt as msm

view = viewer.demo["dialanine"]
second_dialanine = msm.copy(view.molsys)
msm.structure.translate(second_dialanine, "[2.0, 0.0, 0.0] nm", in_place=True)
view.add(second_dialanine)
view.show()
view.write_html("../_static/views/two_demo_dialanine.html", title="2 Dialanines", mode="lite")
