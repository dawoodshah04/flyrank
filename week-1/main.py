from http.client import HTTPException

from fastapi import FastAPI
import uuid


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
