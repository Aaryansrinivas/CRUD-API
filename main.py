
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import database
 
app = FastAPI()
 
# In-memory "database" — a plain Python list. Data resets whenever the server restarts.
tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Write README", "done": False},
    {"id": 3, "title": "Learn FastAPI", "done": True},
]
next_id = 4
 
 
class TaskCreate(BaseModel):
    title: Optional[str] = None
 
 
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None
 
 
@app.get("/", summary="API info")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}
 
 
@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}
 
 
@app.get("/tasks")
def get_tasks():

    cursor = database.connection.cursor()

    cursor.execute("SELECT * FROM tasks")

    rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "title": row[1],
            "done": bool(row[2])
        }
        for row in rows
    ]
 
@app.get("/tasks/{task_id}")
def get_task(task_id: int):

    cursor = database.connection.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id=?",
        (task_id,)
    )

    row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {
        "id": row[0],
        "title": row[1],
        "done": bool(row[2])
    }
 
 
@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):

    if task.title.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Title required"
        )

    cursor = database.connection.cursor()

    cursor.execute(
        "INSERT INTO tasks(title, done) VALUES(?, ?)",
        (task.title, False)
    )

    database.connection.commit()

    task_id = cursor.lastrowid

    return {
        "id": task_id,
        "title": task.title,
        "done": False
    }
 
 
@app.put("/tasks/{task_id}", summary="Update a task's title and/or done status")
def update_task(task_id: int, update: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            if update.title is not None and not update.title.strip():
                raise HTTPException(status_code=400, detail="Title cannot be empty")
            if update.title is not None:
                task["title"] = update.title.strip()
            if update.done is not None:
                task["done"] = update.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
 
 
@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.get("/stats", summary="Task statistics")
def stats():
    total = len(tasks)
    done = len([t for t in tasks if t["done"]])
    return {"total": total, "done": done, "open": total - done}


@app.post("/reset", summary="Reset tasks to seed data")
def reset():
    global tasks, next_id
    tasks = [
        {"id": 1, "title": "Buy milk", "done": False},
        {"id": 2, "title": "Write README", "done": False},
        {"id": 3, "title": "Learn FastAPI", "done": True},
    ]
    next_id = 4
    return {"status": "reset"}