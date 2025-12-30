import molsysviewer as viewer

view = viewer.demo["1TCD"]
view.show()
view.write_html("../_static/views/demo_1TCD.html", title="1TCD", mode="lite")
