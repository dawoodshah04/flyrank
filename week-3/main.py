import sqlite3
from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel


DATABASE_PATH = Path(__file__).with_name("tasks.db")


def initialize_database() -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1))
            )
            """
        )
        task_count = connection.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if task_count == 0:
            connection.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                [("get request", 1), ("POST:id request", 1), ("POST request", 0)],
            )


def task_from_row(row: sqlite3.Row) -> dict:
    return {"id": row[0], "title": row[1], "done": bool(row[2])}


initialize_database()


class TaskCreate(BaseModel):
    title: str
    done: bool = False


class TaskUpdate(BaseModel):
    title: str
    done: bool


app = FastAPI()


tasks = [
    {"id": 1, "title": "get request", "done": True},
    {"id": 2, "title": "POST:id request", "done": True},
    {"id": 3, "title": "POST request", "done": False},
]


@app.get("/")
async def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/tasks")
async def list_tasks():
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute("SELECT * FROM tasks").fetchall()
    return [task_from_row(row) for row in rows]


@app.get("/tasks/{id}")
async def get_task(id: int):
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchone()
    if row is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return task_from_row(row)


@app.post("/tasks")
async def create_task(task: TaskCreate, res: Response):
    if not task.title or task.title.strip() == "":
        raise HTTPException(status_code=400, detail="Title required")

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (task.title, 0),
        )
        new_task = {
            "id": cursor.lastrowid,
            "title": task.title,
            "done": False,
        }

    res.status_code = 201
    return {"message": "done, here's your receipt", "data": new_task, "status_code": 201}


@app.put("/tasks/{id}")
async def update_task(task: TaskUpdate, id: int):
    if not task.title or task.title.strip() == "":
        raise HTTPException(status_code=400, detail="Title required")
    for stored_task in tasks:
        if stored_task["id"] == id:
            stored_task["title"] = task.title
            stored_task["done"] = task.done
            return {"message": f"Task{id} updated", "status_code": 200, "data": stored_task}
    raise HTTPException(status_code=404, detail=f"Task {id} not found")


@app.delete("/tasks/{id}")
async def delete_task(id: int):
    for task in tasks:
        if task["id"] == id:
            tasks.remove(task)
            return Response(status_code=204)
    raise HTTPException(status_code=404, detail=f"Task {id} not found")