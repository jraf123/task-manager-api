from __future__ import annotations
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

DB_PATH = os.environ.get('TASK_DB', 'tasks.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        completed INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
      )""")
    conn.commit()
    return conn

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default='', max_length=2000)

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool | None = None

class Task(TaskCreate):
    id: int
    completed: bool
    created_at: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    with get_db() as conn: pass
    yield

app = FastAPI(title='TaskFlow API', version='1.0.0', lifespan=lifespan,
              description='A lightweight SQLite-backed task management REST API.')

def as_task(row):
    return Task(id=row['id'], title=row['title'], description=row['description'],
                completed=bool(row['completed']), created_at=row['created_at'])

def fetch(conn, task_id):
    row = conn.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
    if row is None:
        raise HTTPException(404, detail='Task not found')
    return row

@app.get('/health')
def health(): return {'status': 'ok'}

@app.post('/tasks', response_model=Task, status_code=201)
def create_task(data: TaskCreate):
    title = data.title.strip()
    if not title: raise HTTPException(422, detail='Title cannot be blank')
    with get_db() as conn:
        cursor = conn.execute('INSERT INTO tasks (title,description,created_at) VALUES (?,?,?)',
            (title, data.description, datetime.now(timezone.utc).isoformat()))
        return as_task(fetch(conn, cursor.lastrowid))

@app.get('/tasks', response_model=list[Task])
def list_tasks(completed: bool | None = None, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    with get_db() as conn:
        if completed is None:
            rows = conn.execute('SELECT * FROM tasks ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset)).fetchall()
        else:
            rows = conn.execute('SELECT * FROM tasks WHERE completed=? ORDER BY id DESC LIMIT ? OFFSET ?', (int(completed), limit, offset)).fetchall()
        return [as_task(row) for row in rows]

@app.get('/tasks/{task_id}', response_model=Task)
def get_task(task_id: int):
    with get_db() as conn: return as_task(fetch(conn, task_id))

@app.patch('/tasks/{task_id}', response_model=Task)
def update_task(task_id: int, data: TaskUpdate):
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, detail='No fields provided')
    if 'title' in changes:
        if changes['title'] is None or not changes['title'].strip():
            raise HTTPException(422, detail='Title cannot be blank')
        changes['title'] = changes['title'].strip()
    if any(v is None for v in changes.values()):
        raise HTTPException(422, detail='Fields cannot be null')
    if 'completed' in changes: changes['completed'] = int(changes['completed'])
    with get_db() as conn:
        fetch(conn, task_id)
        columns = ', '.join(f'{key}=?' for key in changes)
        conn.execute(f'UPDATE tasks SET {columns} WHERE id=?', (*changes.values(), task_id))
        return as_task(fetch(conn, task_id))

@app.delete('/tasks/{task_id}', status_code=204)
def delete_task(task_id: int):
    with get_db() as conn:
        fetch(conn, task_id)
        conn.execute('DELETE FROM tasks WHERE id=?', (task_id,))
