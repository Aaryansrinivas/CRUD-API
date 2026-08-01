from typing import Optional
from app.repository import TaskRepository
from app.db import get_connection


class PostgresTaskRepository(TaskRepository):
    """Real persistence: every method here maps to one SQL statement.
    Notice the method signatures are identical to InMemoryTaskRepository —
    that's what lets main.py swap one for the other with a one-line change."""

    def list(self, done: Optional[bool] = None, search: Optional[str] = None) -> list[dict]:
        query = "SELECT id, title, done FROM tasks"
        clauses = []
        params = []

        if done is not None:
            clauses.append("done = %s")
            params.append(done)
        if search is not None:
            clauses.append("title ILIKE %s")
            params.append(f"%{search}%")

        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id"

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

    def get(self, task_id: int) -> Optional[dict]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def create(self, title: str) -> dict:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done",
                    (title, False),
                )
                return dict(cur.fetchone())

    def update(self, task_id: int, title: Optional[str] = None, done: Optional[bool] = None) -> Optional[dict]:
        existing = self.get(task_id)
        if existing is None:
            return None

        new_title = title if title is not None else existing["title"]
        new_done = done if done is not None else existing["done"]

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done",
                    (new_title, new_done, task_id),
                )
                return dict(cur.fetchone())

    def delete(self, task_id: int) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
                return cur.rowcount > 0
