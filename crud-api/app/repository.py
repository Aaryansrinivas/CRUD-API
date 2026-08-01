"""
The Repository interface.

Both the in-memory store (from A2) and the Postgres store implement
this exact same set of methods. The service layer and routes only ever
talk to this interface — they never know or care which one is plugged in.
That's the whole point of this assignment: swapping the implementation
in main.py is the only change needed to move from memory to Postgres.
"""

from abc import ABC, abstractmethod
from typing import Optional


class TaskRepository(ABC):
    @abstractmethod
    def list(self, done: Optional[bool] = None, search: Optional[str] = None) -> list[dict]:
        ...

    @abstractmethod
    def get(self, task_id: int) -> Optional[dict]:
        ...

    @abstractmethod
    def create(self, title: str) -> dict:
        ...

    @abstractmethod
    def update(self, task_id: int, title: Optional[str] = None, done: Optional[bool] = None) -> Optional[dict]:
        ...

    @abstractmethod
    def delete(self, task_id: int) -> bool:
        ...
