# Task API

## Stage 4: SQLite SQL Checkpoint

The API and `week-3/tasks.db` use the same SQLite file. A query run directly against the database was:

```sql
SELECT COUNT(*) FROM tasks;
```

It returned `3`, matching the three seeded tasks served by `GET /tasks`.

A direct update such as `UPDATE tasks SET done = 1 WHERE id = 3;` is visible through the API immediately because both DB Browser for SQLite and FastAPI read the same database file.