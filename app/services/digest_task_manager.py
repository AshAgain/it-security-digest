from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


TaskStatus = Literal[
    "pending",
    "collecting",
    "analyzing",
    "generating",
    "completed",
    "failed",
]


@dataclass
class DigestTask:
    status: TaskStatus = "pending"
    current: int = 0
    total: int = 0
    percent: int = 0
    message: str = "Подготовка..."
    error: str | None = None
    result: object | None = None


_tasks: dict[str, DigestTask] = {}


def create_task(task_id: str) -> DigestTask:
    task = DigestTask()
    _tasks[task_id] = task
    return task


def get_task(task_id: str) -> DigestTask | None:
    return _tasks.get(task_id)


def update_task(
    task_id: str,
    *,
    status: TaskStatus | None = None,
    current: int | None = None,
    total: int | None = None,
    percent: int | None = None,
    message: str | None = None,
    error: str | None = None,
    result: object | None = None,
) -> None:
    task = _tasks.get(task_id)

    if task is None:
        return

    if status is not None:
        task.status = status

    if current is not None:
        task.current = current

    if total is not None:
        task.total = total

    if percent is not None:
        task.percent = percent

    if message is not None:
        task.message = message

    if error is not None:
        task.error = error

    if result is not None:
        task.result = result