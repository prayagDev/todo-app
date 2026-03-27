from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import math
import pymongo
from bson import ObjectId
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
myclient = pymongo.MongoClient(MONGO_URI)
todo_db = myclient["todo_app"]
todo_col = todo_db["todo"]

# --- API ROUTES (Returning HTML for HTMX) ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/tasks", response_class=HTMLResponse)
async def get_tasks(request: Request, status: str = "open", page: int = 1):
    page_size = 10
    skip = (page - 1) * page_size
    query = {"status": status}
    
    cursor = todo_col.find(query).skip(skip).limit(page_size).sort("_id", -1)
    tasks = list(cursor)
    for task in tasks:
        task["_id"] = str(task["_id"])
    
    total = todo_col.count_documents(query)
    total_pages = math.ceil(total / page_size)

    return templates.TemplateResponse("todo_list.html", {
        "request": request,
        "tasks": tasks,
        "status": status,
        "current_page": page,
        "total_pages": total_pages
    })

@app.post("/tasks")
async def create_todo(request: Request, subject: str = Form(...), description: str = Form(...)):
    todo_col.insert_one({"subject": subject, "description": description, "status": "open"})
    # After creating, refresh the list
    return await get_tasks(request, status="open")

@app.get("/tasks/{id}")
async def get_task_details(request: Request, id: str, edit: bool = False):
    task = todo_col.find_one({"_id": ObjectId(id)})
    task["_id"] = str(task["_id"])
    template = "todo_edit.html" if edit else "todo_detail.html"
    return templates.TemplateResponse(template, {"request": request, "task": task})

@app.post("/tasks/update/{id}")
async def update_task(request: Request, id: str, subject: str = Form(...), description: str = Form(...)):
    todo_col.update_one({"_id": ObjectId(id)}, {"$set": {"subject": subject, "description": description}})
    return await get_tasks(request)

@app.post("/tasks/complete/{id}")
async def complete_task(request: Request, id: str):
    todo_col.update_one({"_id": ObjectId(id)}, {"$set": {"status": "complete"}})
    return await get_tasks(request)

