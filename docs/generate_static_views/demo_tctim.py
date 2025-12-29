import molsysviewer as viewer

view = viewer.demo.tctim()
view.show()
view.write_html("../_static/views/demo_tctim.html", title="TcTIM", mode="lite")
