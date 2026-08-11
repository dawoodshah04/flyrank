import os
import psycopg2

SEED_TASKS = [("get request", True), ("POST:id request", True), ("POST request", False)]

def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def row_to_task(row):
    return {"id": row[0], "title": row[1], "done": bool(row[2])}

def initialize_database():
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("""CREATE TABLE IF NOT EXISTS tasks (id SERIAL PRIMARY KEY, title TEXT NOT NULL, done BOOLEAN NOT NULL DEFAULT FALSE)""")
        cursor.execute("SELECT COUNT(*) FROM tasks")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO tasks (title, done) VALUES (%s, %s)", SEED_TASKS)

def database_is_healthy():
    try:
        with get_connection() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone()[0] == 1
    except psycopg2.Error:
        return False

def list_tasks():
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT id, title, done FROM tasks ORDER BY id")
        return [row_to_task(row) for row in cursor.fetchall()]

def get_task(task_id):
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
        row = cursor.fetchone()
        return row_to_task(row) if row else None

def create_task(title, done):
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done", (title, done))
        return row_to_task(cursor.fetchone())

def update_task(task_id, title, done):
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done", (title, done, task_id))
        row = cursor.fetchone()
        return row_to_task(row) if row else None

def delete_task(task_id):
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        return cursor.rowcount == 1
