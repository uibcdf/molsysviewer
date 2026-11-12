"""Real View probe: scheduled comm sends require no following browser request."""

import asyncio
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
import molsysviewer as msv


def main():
    transport = runpy.run_path(str(Path(__file__).with_name("canvas-popup-bridge.py")))
    view = msv.demo["dialanine"]

    def action(owner, event):
        if event.get("schedule_comm"):
            loop = asyncio.get_running_loop()
            loop.call_later(0.02, owner.scene.set_background, 0x204060)
            loop.call_later(0.04, owner.scene.set_background, 0x102030)
            return {"scheduled": True}
        if event.get("inline_comm"):
            owner.scene.set_background(0xABCDEF)
            return True
        return False

    transport["serve"](view, action, async_processing="--sync" not in sys.argv)


if __name__ == "__main__":
    main()
