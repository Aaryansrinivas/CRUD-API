from typing import Optional
from app.repository import TaskRepository


class NotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class TaskService:
    """Business rules live here, once, regardless of which repository is
    plugged in underneath. Routes translate these exceptions into HTTP
    status codes; the service itself knows nothing about HTTP."""

    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def list_tasks(self, done: Optional[bool] = None, search: Optional[str] = None) -> list[dict]:
        return self.repository.list(done=done, search=search)

    def get_task(self, task_id: int) -> dict:
        task = self.repository.get(task_id)
        if task is None:
            raise NotFoundError(f"Task {task_id} not found")
        return task

    def create_task(self, title: Optional[str]) -> dict:
        if not title or not title.strip():
            raise ValidationError("Title is required and cannot be empty")
        return self.repository.create(title.strip())

    def update_task(self, task_id: int, title: Optional[str] = None, done: Optional[bool] = None) -> dict:
        if title is not None and not title.strip():
            raise ValidationError("Title cannot be empty")
        updated = self.repository.update(task_id, title=title.strip() if title else None, done=done)
        if updated is None:
            raise NotFoundError(f"Task {task_id} not found")
        return updated

    def delete_task(self, task_id: int) -> None:
        deleted = self.repository.delete(task_id)
        if not deleted:
            raise NotFoundError(f"Task {task_id} not found")
