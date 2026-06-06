from __future__ import annotations


class DummyView:
    def __init__(self):
        self.messages = []

    def _send(self, message):
        self.messages.append(message)


def test_set_legend_emits_items():
    from molsysviewer.scene import SceneManager
    view = DummyView()
    scene = SceneManager(view)

    scene.set_legend([
        {"label": "pocket", "color": 0x0072B2},
        ("channel", 0xE69F00),  # tuple form
    ], position="bottom-left")

    msg = view.messages[-1]
    assert msg["op"] == "set_legend"
    assert msg["options"]["position"] == "bottom-left"
    items = msg["options"]["items"]
    assert items == [
        {"label": "pocket", "color": 0x0072B2},
        {"label": "channel", "color": 0xE69F00},
    ]


def test_set_legend_empty_hides():
    from molsysviewer.scene import SceneManager
    view = DummyView()
    SceneManager(view).set_legend(None)
    msg = view.messages[-1]
    assert msg["op"] == "set_legend"
    assert msg["options"]["items"] == []
