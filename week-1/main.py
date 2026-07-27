from http.client import HTTPException
from pydantic import BaseModel
from fastapi import FastAPI
import uuid

class TaskCreate(BaseModel):
    title:str
    done:bool=False

app = FastAPI()


tasks = [
{
    "id": uuid.uuid4(),
    "title":"get request",
    "done":True

},
{
    "id": uuid.uuid4(),
    "title":"POST:id request",
    "done":True

},
{
    "id": uuid.uuid4(),
    "title":"POST request",
    "done":False

},

]

@app.get('/')
async def root():
    return { "name": "Task API", "version": "1.0", "endpoints": ["/tasks"] }

@app.get('/health')
async def root():
    return {"status":"ok"}

@app.get('/tasks')
async def root():
    return tasks

@app.get('/tasks/{id}')
async def root(id:uuid.UUID):
    for task in tasks:
        if task["id"] == id:
            return task
        raise HTTPException(status_code=404,details=f"Task{id} not Found") 


@app.post('/tasks')
async def create_task(task:TaskCreate):
    new_task = {
        "id" : uuid.uuid4(),
        "title" : task.title,
        "done" : False,
    }

    tasks.append(new_task)

    return new_task

