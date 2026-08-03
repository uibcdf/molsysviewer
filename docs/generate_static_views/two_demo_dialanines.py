import molsysviewer as viewer
import molsysmt as msm
import pyunitwizard as puw

view = viewer.demo["dialanine"]
second_dialanine = msm.copy(view.molsys)
coordinates = msm.get(second_dialanine, element="atom", coordinates=True)
msm.set(second_dialanine, coordinates=coordinates + puw.quantity([2.0, 0.0, 0.0], "nanometer"))
view.load(second_dialanine, mode="add")
view.show()
view.export.html("../_static/views/two_demo_dialanine.html", title="2 Dialanines", shared_runtime="../_static")
