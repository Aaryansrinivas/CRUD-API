from fastapi import FastAPI ,HTTPException

app = FastAPI()

tasks = [
    {"id":1,"title" : "buy milk","done" : "false"},
    {"id":2,"title" : "walk the dog","done" : "false"},
    {"id":3,"title" : "read a book","done" : "true"}
]
@app.get("/")
def root():
    return "default path"

@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id :int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"{task_id} not found")
