import molsysviewer as viewer

view = viewer.demo["181L"]
view.show()
view.export.html("../_static/views/demo_181L.html", title="181L", mode="lite", runtime_assets_dir="../_static")
