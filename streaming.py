"""NDJSON-стриминг прогресса для sync/upload."""

from __future__ import annotations

import json
import queue
import threading
from typing import Any, Callable, Iterator


def ndjson_line(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False) + "\n"


def stream_job(worker: Callable[[Callable[[dict[str, Any]], None]], None]) -> Iterator[str]:
    """Запускает worker(put_event) в потоке и стримит NDJSON из очереди."""
    events: queue.Queue[dict[str, Any] | None] = queue.Queue()

    def put_event(payload: dict[str, Any]) -> None:
        events.put(payload)

    def run() -> None:
        try:
            worker(put_event)
        except Exception as exc:  # noqa: BLE001
            put_event({"type": "error", "message": str(exc)})
        finally:
            events.put(None)

    threading.Thread(target=run, daemon=True).start()
    while True:
        item = events.get()
        if item is None:
            break
        yield ndjson_line(item)
