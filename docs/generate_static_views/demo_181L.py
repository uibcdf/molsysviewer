import molsysviewer as msv

view = msv.demo["181L"]
view.show()
view.export.html("../_static/views/demo_181L.html", title="181L", shared_runtime="../_static", background="transparent")
