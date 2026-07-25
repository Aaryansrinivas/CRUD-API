
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
 
 
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):

    cursor = database.connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET title=?, done=?
        WHERE id=?
        """,
        (task.title, task.done, task_id)
    )

    if cursor.rowcount == 0:
        raise HTTPException(404, "Task not found")

    database.connection.commit()

    return {
        "id": task_id,
        "title": task.title,
        "done": task.done
    }
  
 
 
@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    cursor = database.connection.cursor()
    cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    database.connection.commit()
    if cursor.rowcount == 0:
        raise HTTPException(404, "Task not found")
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