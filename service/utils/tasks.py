"""Disk-based task state management."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from service.config import settings
from service.schemas.models import Task, TaskStatus, TaskStep, StepStatus

TASKS_DIR = Path(settings.tasks_dir)


def generate_task_id() -> str:
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"gen_{ts}_{suffix}"


def _task_path(task_id: str) -> Path:
    return TASKS_DIR / f"{task_id}.json"


def create_task(project_id: str, steps: list[str]) -> Task:
    task = Task(
        task_id=generate_task_id(),
        project_id=project_id,
        status=TaskStatus.pending,
        steps=[TaskStep(name=s) for s in steps],
    )
    task.touch()
    save_task(task)
    return task


def save_task(task: Task):
    task.touch()
    data = task.model_dump()
    _task_path(task.task_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_task(task_id: str) -> Optional[Task]:
    path = _task_path(task_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Task(**data)
    except (json.JSONDecodeError, KeyError):
        return None


def load_all_tasks() -> list[Task]:
    tasks = []
    for p in sorted(TASKS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            tasks.append(Task(**data))
        except (json.JSONDecodeError, KeyError):
            continue
    return tasks


def update_task_status(task: Task, status: TaskStatus, progress: Optional[float] = None, current_step: Optional[str] = None):
    task.status = status
    if progress is not None:
        task.progress = progress
    if current_step is not None:
        task.current_step = current_step
    save_task(task)


def update_step(task: Task, step_index: int, status: StepStatus, detail: str = ""):
    if 0 <= step_index < len(task.steps):
        task.steps[step_index].status = status
        task.steps[step_index].detail = detail
    save_task(task)


def set_task_error(task: Task, error: str):
    task.status = TaskStatus.failed
    task.error = error
    save_task(task)


def set_task_result(task: Task, result: dict):
    task.status = TaskStatus.completed
    task.progress = 1.0
    task.result = result
    save_task(task)


def delete_task(task_id: str):
    path = _task_path(task_id)
    if path.exists():
        path.unlink()
