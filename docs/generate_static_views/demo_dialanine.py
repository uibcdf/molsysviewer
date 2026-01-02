import molsysviewer as viewer

view = viewer.demo["dialanine"]
view.show()
view.write_html("../_static/views/demo_dialanine.html", title="Dialanine", mode="lite")
