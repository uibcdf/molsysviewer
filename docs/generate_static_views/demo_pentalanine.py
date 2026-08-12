import molsysviewer as msv

view = msv.demo["pentalanine"]
view.show()
view.export.html("../_static/views/demo_pentalanine.html", title="Pentalanine", shared_runtime="../_static", background="transparent")
