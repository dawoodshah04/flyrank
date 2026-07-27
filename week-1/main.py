from http.client import HTTPException
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi import Response
import uuid


class TaskCreate(BaseModel):
    title:str
    done:bool=False

class TaskUpdate(BaseModel):
    title:str
    done:bool


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
async def create_task(task:TaskCreate, res:Response):
    
    new_task = {
        "id" : uuid.uuid4(),
        "title" : task.title,
        "done" : False,
    }
    tasks.append(new_task)
    if not new_task:
        raise HTTPException(status_code=404,details=f"Task Name not added")

    res.status_code = 201

    return {
        "message": "done, here's your receipt",
        "data": new_task,
        "status_code":201
    }


@app.put('/tasks/{id}')
async def update_res(task: TaskUpdate,id:uuid.UUID):
    if not task.title or task.title.strip() == "":
        raise HTTPException(status_code=400, detail=f"Title required")
    for t in tasks:
        if t["id"] == id:
            t["title"] = task.title
            t["done"] = task.done
            return {"message":f"Task{id} updated","status_code":201,"data":t}

    #task not found 
    raise HTTPException(status_code=404, detail=f"Task {id} not Found")


@app.delete('/tasks/{id}')
async def delete_task(id:uuid.UUID):
    for t in tasks:
        if t["id"] == id:
            tasks.remove(t)
            return {"message":"No Content",'status_code':201}

    raise HTTPException(status_code=404, detail=f"Unknow id:{id}")
 