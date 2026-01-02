import molsysviewer as viewer

view = viewer.demo["pentalanine"]
view.remove(structure_indices=[0, 1, 2])
view.show()
view.write_html("../_static/views/demo_pentalanine_removed_structures.html", title="Pentalanine", mode="lite")
