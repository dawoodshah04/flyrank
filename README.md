# Task API — containerized Postgres

This FastAPI CRUD service stores tasks in PostgreSQL. Docker Compose starts the API and database together.

## Run

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The API is available at `http://localhost:3000`. `.env` is ignored by Git; `.env.example` documents the required variables. The app creates `tasks` automatically and seeds three tasks only when the table is empty. The Compose `taskdata` volume preserves rows across restarts.

## Endpoints

| Method | Path | Result |
| --- | --- | --- |
| GET | `/tasks` | List tasks (`200`) |
| GET | `/tasks/{id}` | Read one (`200` or `404`) |
| POST | `/tasks` | Create (`201`, empty title `400`) |
| PUT | `/tasks/{id}` | Update (`200`, invalid/unknown `400`/`404`) |
| DELETE | `/tasks/{id}` | Delete (`204` or `404`) |
| GET | `/health` | API/database health (`200`) |

Example checkpoint:

```text
> curl.exe -i http://localhost:3000/tasks/999
HTTP/1.1 404 Not Found
content-type: application/json

{"error":"Task not found"}
```

Database checkpoint:

```powershell
docker exec taskdb psql -U postgres -d tasks -c "\dt"
docker exec taskdb psql -U postgres -d tasks -c "SELECT * FROM tasks;"
```

All SQL input uses psycopg2 parameter placeholders (`%s`); user values are never concatenated into SQL strings.
