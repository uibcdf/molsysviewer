import molsysviewer as viewer
import molsysmt as msm
import pyunitwizard as puw

view = viewer.demo["dialanine"]
second_structure = msm.copy(view.molsys)
coordinates = msm.get(second_structure, element="atom", coordinates=True)
msm.set(second_structure, coordinates=coordinates + puw.quantity([0.2, 0.0, 0.0], "nanometer"))
view.load(second_structure, mode="append_structures")
view.show()
view.export.html("../_static/views/two_structures_dialanine.html", title="Dialanine (2 structures)", mode="lite")
