import {Pool} from 'pg';
import dotenv from "dotenv"
dotenv.config()

const pool = new Pool({
    connectionString: process.env.DATABASE_URL
    
})


export interface Task{
    id: number,
    title:string,
    done:boolean
}

export async function getTasks():Promise<Task[]>{
    const result = await pool.query("SELECT * FROM tasks ORDER BY id")
    return result.rows;
}

export async function getTaskById(id:number):Promise<Task | null>{
    const result = await pool.query("SELECT * FROM tasks WHERE id = $1",[id])

    return result.rows[0]??null
}

export async function createTask(title:string,done:boolean):Promise<Task>{
    const result = await pool.query("INSERT INTO tasks (title,done) VALUES ($1,$2) RETURNING *",[title,done]);

    return result.rows[0];
}

export async function updateTask(title:string,done:boolean,id:number):Promise<Task | null>{
    const result = await pool.query("UPDATE tasks SET title=$1, done=$2 WHERE id=$3 RETURNING *",[title,done,id])

    return result.rows[0]??null;
}

export async function deleteTask(id: number): Promise<boolean> {
  const result = await pool.query(
    "DELETE FROM tasks WHERE id = $1",
    [id]
  );

  return result.rowCount === 1;
}

export async function initializeDatabase() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS tasks (
      id SERIAL PRIMARY KEY,
      title TEXT NOT NULL,
      done BOOLEAN NOT NULL DEFAULT FALSE
    )
  `);

  const result = await pool.query(
    "SELECT COUNT(*) FROM tasks"
  );

  if (Number(result.rows[0].count) === 0) {
    await pool.query(`
      INSERT INTO tasks (title, done)
      VALUES
        ('Learn Docker', false),
        ('Connect PostgreSQL', false),
        ('Containerize the API', false)
    `);
  }
}