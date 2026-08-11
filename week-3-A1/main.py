import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from repository import create_task, delete_task, get_task, initialize_database, list_tasks, update_task, database_is_healthy

load_dotenv()
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not configured")
initialize_database()

class TaskCreate(BaseModel):
    title: str
    done: bool = False

class TaskUpdate(BaseModel):
    title: str
    done: bool

app = FastAPI()

@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health():
    if not database_is_healthy():
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok", "db": "ok"}

@app.get("/tasks")
def read_tasks():
    return list_tasks()

@app.get("/tasks/{task_id}")
def read_task(task_id: int):
    task = get_task(task_id)
    if task is None:
        return Response(content='{"error":"Task not found"}', status_code=404, media_type="application/json")
    return task

@app.post("/tasks", status_code=201)
def add_task(task: TaskCreate):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title required")
    new_task = create_task(task.title, task.done)
    return {"message": "done, here's your receipt", "data": new_task, "status_code": 201}

@app.put("/tasks/{task_id}")
def edit_task(task_id: int, task: TaskUpdate):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title required")
    updated = update_task(task_id, task.title, task.done)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"message": f"Task{task_id} updated", "status_code": 200, "data": updated}

@app.delete("/tasks/{task_id}", status_code=204)
def remove_task(task_id: int):
    if not delete_task(task_id):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return Response(status_code=204)
