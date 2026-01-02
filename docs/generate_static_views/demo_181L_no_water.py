import molsysviewer as viewer

view = viewer.demo["181L"]
view.remove(selection='molecule_type=="water"')
view.show()
view.write_html("../_static/views/demo_181L_no_water.html", title="181L", mode="lite")
