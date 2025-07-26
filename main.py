import os
from fastapi import FastAPI, Form, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from pydantic import BaseModel
from functools import lru_cache

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Model definition
class Todo(BaseModel):
    id: int
    task: str
    owner: str

# In-memory storage
todos: List[Todo] = []

@lru_cache(maxsize=128)
def get_cached_todos():
    return todos

# API endpoints
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    cached_todos = get_cached_todos()
    return templates.TemplateResponse("index.html", {"request": request, "todos": cached_todos})

@app.post("/create-todo")
async def create_todo(task: str = Form(...), owner: str = Form(...)):
    todo_id = len(todos) + 1
    new_todo = Todo(id=todo_id, task=task, owner=owner)
    todos.append(new_todo)
    get_cached_todos.cache_clear()
    return RedirectResponse("/", status_code=303)

@app.get("/todos", response_class=HTMLResponse)
async def get_todos(request: Request, owner: Optional[str] = Query(None)):
    cached_todos = get_cached_todos()
    if owner:
        filtered_todos = [todo for todo in cached_todos if todo.owner == owner]
        return templates.TemplateResponse("todos.html", {"request": request, "todos": filtered_todos, "owner": owner})
    return templates.TemplateResponse("todos.html", {"request": request, "todos": cached_todos, "owner": None})

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, owner: str = Form(...)):
    for todo in todos:
        if todo.id == todo_id and todo.owner == owner:
            todos.remove(todo)
            get_cached_todos.cache_clear()  # Clear cache when data changes
            return RedirectResponse("/todos?owner=" + owner, status_code=303)
    raise HTTPException(status_code=404, detail="Todo not found or unauthorized")

@app.post("/todos/{todo_id}")
def handle_todo_action(todo_id: int, method: str = Form(...), task: Optional[str] = Form(None), owner: str = Form(...)):
    if method == "put":
        # Handle Edit
        for todo in todos:
            if todo.id == todo_id and todo.owner == owner:
                todo.task = task  # Update the task
                get_cached_todos.cache_clear()  # Clear cache when data changes
                return RedirectResponse(f"/todos?owner={owner}", status_code=303)
        raise HTTPException(status_code=404, detail="Todo not found or unauthorized")
    elif method == "delete":
        # Handle Delete
        for todo in todos:
            if todo.id == todo_id and todo.owner == owner:
                todos.remove(todo)
                get_cached_todos.cache_clear()  # Clear cache when data changes
                return RedirectResponse("/todos?owner=" + owner, status_code=303)
        raise HTTPException(status_code=404, detail="Todo not found or unauthorized")
    raise HTTPException(status_code=400, detail="Invalid method")
