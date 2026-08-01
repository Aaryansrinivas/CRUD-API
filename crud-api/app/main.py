import os
from dotenv import load_dotenv
load_dotenv()  # reads .env into environment variables before anything else runs

from fastapi import FastAPI, HTTPException
from typing import Optional

from app.models import TaskCreate, TaskUpdate
from app.service import TaskService, NotFoundError, ValidationError
from app.memory_repository import InMemoryTaskRepository
from app.postgres_repository import PostgresTaskRepository

app = FastAPI()

# --- The one line that decides where data lives ---------------------------
# REPO_TYPE=postgres (default) -> real, persistent Postgres storage
# REPO_TYPE=memory             -> the old A2 in-memory store, for comparison
# Nothing below this block, and nothing in service.py, changes either way.
REPO_TYPE = os.environ.get("REPO_TYPE", "postgres")
repository = PostgresTaskRepository() if REPO_TYPE == "postgres" else InMemoryTaskRepository()
service = TaskService(repository)
# ----------------------------------------------------------------------------


@app.get("/", summary="API info")
def root():
    return {"name": "Task API", "version": "2.0", "storage": REPO_TYPE, "endpoints": ["/tasks"]}


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


@app.get("/tasks", summary="List all tasks (with optional filters)")
def get_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    return service.list_tasks(done=done, search=search)


@app.get("/tasks/{task_id}", summary="Get a single task by id")
def get_task(task_id: int):
    try:
        return service.get_task(task_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/tasks", status_code=201, summary="Create a new task")
def create_task(task: TaskCreate):
    try:
        return service.create_task(task.title)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/tasks/{task_id}", summary="Update a task's title and/or done status")
def update_task(task_id: int, update: TaskUpdate):
    try:
        return service.update_task(task_id, title=update.title, done=update.done)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    try:
        service.delete_task(task_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
