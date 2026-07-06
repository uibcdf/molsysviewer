import molsysviewer as viewer

view = viewer.demo["pentalanine"]
view.show()
view.export.html("../_static/views/demo_pentalanine.html", title="Pentalanine", mode="lite")
