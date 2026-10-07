# TaskFlow — REST API Task Manager

A production-style learning project: a documented Python REST API with SQLite persistence, Pydantic validation and automated endpoint tests.

## Features
- Create, read, update and delete tasks
- Filter by completion status
- Pagination with `limit` and `offset`
- Request validation and meaningful 404/422 responses
- Auto-generated OpenAPI/Swagger documentation
- Persistent SQLite database; isolated temporary databases for tests

## Run locally
```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn task_api.main:app --reload
```
Visit http://127.0.0.1:8000/docs to try the API in your browser.

## Example requests
```bash
curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"title":"Build my portfolio","description":"Ship three projects"}'
curl http://127.0.0.1:8000/tasks
curl -X PATCH http://127.0.0.1:8000/tasks/1 -H "Content-Type: application/json" -d '{"completed":true}'
curl -X DELETE http://127.0.0.1:8000/tasks/1
```

## Tests
```bash
python -m pytest -q
```

## API routes
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/tasks` | Create task |
| GET | `/tasks` | List/filter/paginate tasks |
| GET | `/tasks/{id}` | Fetch one task |
| PATCH | `/tasks/{id}` | Update selected fields |
| DELETE | `/tasks/{id}` | Delete task |

## Scope and next steps
This is a local demonstration API, not a deployed multi-user product. It has no authentication or rate limiting. Add user accounts and PostgreSQL before exposing it publicly.

## Skills demonstrated
REST design, FastAPI, SQL, Pydantic validation, HTTP status codes, integration tests.
