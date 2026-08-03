import molsysviewer as viewer

view = viewer.demo["dialanine"]
view.show()
view.export.html("../_static/views/demo_dialanine.html", title="Dialanine", shared_runtime="../_static")
