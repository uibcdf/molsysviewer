from pathlib import Path

import molsysviewer as viewer


view = viewer.demo['181L']
view.zoom('molecule_name=="BENZENE"')
view.show()
view.export.html("../_static/views/181L_benzene_only_zoom.html", title="181L", mode="lite", runtime_assets_dir="../_static")
