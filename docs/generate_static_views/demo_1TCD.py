import molsysviewer as viewer

view = viewer.demo["1TCD"]
view.show()
view.export.html("../_static/views/demo_1TCD.html", title="1TCD", shared_runtime="../_static")
