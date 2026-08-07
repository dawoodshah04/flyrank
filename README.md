# Task API

A FastAPI CRUD service backed by SQLite. The API keeps the same task endpoints while storing data in `week-3/tasks.db`, so tasks persist across server restarts.

## Why SQLite

SQLite was chosen because it is a single local file, requires no separate database server, needs zero setup, and preserves data after the application stops and starts again.

## Run

From the repository root, run:

```powershell
cd week-3
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8001
```

Then open `http://127.0.0.1:8001/docs` for the interactive API documentation or call `GET /tasks` directly.

The database file is `week-3/tasks.db`. It is created automatically when the application starts, along with the `tasks` table and three seed tasks when the table is empty. The file is ignored by Git so each clone starts with its own database.

## Endpoints

- `GET /tasks` lists tasks from SQLite.
- `GET /tasks/{id}` reads one task with a parameterized query.
- `POST /tasks` creates a task and returns `201`.
- `PUT /tasks/{id}` updates a task and returns `200`.
- `DELETE /tasks/{id}` deletes a task and returns an empty `204` response.

Empty titles return `400`; unknown task IDs return `404`.

## SQLite checkpoint

A query run directly against the database was:

```sql
SELECT COUNT(*) FROM tasks;
```

It returned `3`, matching the three seeded tasks served by `GET /tasks`.

A direct update such as the following appeared through the API immediately without restarting the server because DB Browser for SQLite and FastAPI read the same file:

```sql
UPDATE tasks SET done = 1 WHERE id = 3;
```

The database can be opened in DB Browser for SQLite to inspect the `tasks` table and run these queries. DB Browser was not available in the development environment, so no screenshot is included here.