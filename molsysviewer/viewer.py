from .widget import MolSysViewerWidget

class MolSysViewer:
    def __init__(self):
        self.widget = MolSysViewerWidget()

    def show(self):
        return self.widget

    def show_test_sphere(self):
        self.widget.send({"op": "test_sphere"})
