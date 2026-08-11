import {Pool} from 'pg';

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
    const result = await pool.query("UPDATE tasks SET title=$1 done=$2 WHERE id=$3",[title,done,id])

    return result.rows[0]??null;
}

export async function deleteTask(id: number): Promise<boolean> {
  const result = await pool.query(
    "DELETE FROM tasks WHERE id = $1",
    [id]
  );

  return result.rowCount === 1;
}