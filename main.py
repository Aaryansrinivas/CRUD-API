from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
 
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
 
 
@app.get("/tasks", summary="List all tasks (with optional filters)")
def get_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    result = tasks
    if done is not None:
        result = [t for t in result if t["done"] == done]
    if search is not None:
        result = [t for t in result if search.lower() in t["title"].lower()]
    return result
 
 
@app.get("/tasks/{task_id}", summary="Get a single task by id")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
 
 
@app.post("/tasks", status_code=201, summary="Create a new task")
def create_task(task: TaskCreate):
    global next_id
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")
    new_task = {"id": next_id, "title": task.title.strip(), "done": False}
    tasks.append(new_task)
    next_id += 1
    return new_task
