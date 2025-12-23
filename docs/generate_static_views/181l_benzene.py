from pathlib import Path

import molsysviewer as viewer


view = viewer.load('181L', selection='molecule_type not in ["water", "ion"]')
region_1 = view.new_region('all within 9 angstroms of molecule_name=="BENZENE"', representation='sticks')
view.zoom('molecule_name=="BENZENE"')

camera_snapshot = {
    'mode': 'perspective',
    'fov': 0.7853981633974483,
    'position': [33.70566533935736, -2.8023437337061745, 18.882755226605074],
    'up': [0.1445312180996829, 0.8739959558312091, 0.4639415870401301],
    'target': [26.911489856486416, 6.126255176505263, 4.179204023614221],
    'radius': 7.077834488226701,
    'radiusMax': 72.78181150350126,
    'fog': 15,
    'clipFar': True,
    'minNear': 1,
    'minFar': 0
}
view.set_camera_snapshot(camera_snapshot)
view.show()
view.write_html("../_static/views/181l_benzene.html", title="181L", mode="lite")
