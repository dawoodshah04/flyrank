import {Pool} from 'pg';

const pool = new Pool({
    connectionString: process.env.DATABASE_URL
})

export interface Task{
    id: number,
    title:string,
    done:boolean
}

export async function getTasks(){
    const result = await pool.query("
        SELECT * FROM tasks ORDER BY id")
}