"""События прогресса для live-лога синка/upload."""

from __future__ import annotations

from typing import Any, Callable, Literal, TypedDict


ProgressStage = Literal[
    "start",
    "auth",
    "list",
    "fetch",
    "classify",
    "parse",
    "build",
    "done",
    "error",
    "warn",
]


class ProgressEvent(TypedDict, total=False):
    stage: ProgressStage
    message: str
    current: int
    total: int
    company: str
    detail: str


ProgressCb = Callable[[ProgressEvent], None]


def emit(
    cb: ProgressCb | None,
    stage: ProgressStage,
    message: str,
    **extra: Any,
) -> None:
    if cb is None:
        return
    event: ProgressEvent = {"stage": stage, "message": message}
    for key, value in extra.items():
        if value is not None:
            event[key] = value  # type: ignore[literal-required]
    cb(event)
