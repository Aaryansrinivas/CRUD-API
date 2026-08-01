from typing import Optional
from app.repository import TaskRepository


class InMemoryTaskRepository(TaskRepository):
    """The original A1/A2 store: a plain Python list. Wiped on restart —
    kept here so you can prove, by swapping one line in main.py, that
    the service and routes don't change at all."""

    def __init__(self):
        self._tasks = [
            {"id": 1, "title": "Buy milk", "done": False},
            {"id": 2, "title": "Write README", "done": False},
            {"id": 3, "title": "Learn FastAPI", "done": True},
        ]
        self._next_id = 4

    def list(self, done: Optional[bool] = None, search: Optional[str] = None) -> list[dict]:
        result = self._tasks
        if done is not None:
            result = [t for t in result if t["done"] == done]
        if search is not None:
            result = [t for t in result if search.lower() in t["title"].lower()]
        return result

    def get(self, task_id: int) -> Optional[dict]:
        for task in self._tasks:
            if task["id"] == task_id:
                return task
        return None

    def create(self, title: str) -> dict:
        task = {"id": self._next_id, "title": title, "done": False}
        self._tasks.append(task)
        self._next_id += 1
        return task

    def update(self, task_id: int, title: Optional[str] = None, done: Optional[bool] = None) -> Optional[dict]:
        task = self.get(task_id)
        if task is None:
            return None
        if title is not None:
            task["title"] = title
        if done is not None:
            task["done"] = done
        return task

    def delete(self, task_id: int) -> bool:
        for i, task in enumerate(self._tasks):
            if task["id"] == task_id:
                self._tasks.pop(i)
                return True
        return False
