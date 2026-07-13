"""Measure pre-ready message history overhead without a browser.

Run from the repository root with ``python benchmarks/message_queue.py``.
"""

from __future__ import annotations

import json
from time import perf_counter

from molsysviewer.demo import demo


MESSAGE_COUNT = 30


def main() -> None:
    view = demo["pentalanine"]
    history_before = len(view._message_history)  # noqa: SLF001
    initial_before = list(view.widget.initial_messages)
    sent = []
    view.widget.send = lambda message: sent.append(message)  # type: ignore[method-assign]

    started = perf_counter()
    for index in range(MESSAGE_COUNT):
        view._send({"op": "benchmark_noop", "index": index})  # noqa: SLF001
    elapsed_ms = (perf_counter() - started) * 1000.0

    print(json.dumps({
        "messages": MESSAGE_COUNT,
        "historyBefore": history_before,
        "historyAfter": len(view._message_history),  # noqa: SLF001
        "sentBeforeReady": len(sent),
        "initialMessagesChanged": view.widget.initial_messages != initial_before,
        "totalMs": round(elapsed_ms, 3),
        "msPerMessage": round(elapsed_ms / MESSAGE_COUNT, 3),
    }))


if __name__ == "__main__":
    main()
