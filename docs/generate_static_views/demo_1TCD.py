import molsysviewer as msv

view = msv.demo["1TCD"]
view.show()
view.export.html("../_static/views/demo_1TCD.html", title="1TCD", shared_runtime="../_static", background="transparent")
