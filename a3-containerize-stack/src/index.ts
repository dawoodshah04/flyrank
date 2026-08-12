import express from "express"
import dotenv from "dotenv"
import { getTaskById,
    createTask,deleteTask
    ,updateTask,getTasks,
    initializeDatabase, 
  } from "./repository/taskRepository.js";
import morgan from "morgan"


dotenv.config()

const app = express()
app.use(morgan('dev'))

app.use(express.json())

app.get("/tasks", async (_req, res) => {
  try {
    
    const tasks = await getTasks();
    if(!tasks){
      initializeDatabase()
    }
    return res.status(200).json(tasks);
  } catch (error) {
    console.error(error);

    return res.status(500).json({
      error: "Internal server error",
    });
  }
});

app.post('/tasks',async(_req, res)=>{
    try {
        const {title, done=false} = _req.body;

        if ( typeof title !== "string" ||
      title.trim() === "") {
            
            return res.status(400).json({"message":"Title is required"})
        }

        const task = await createTask(title.trim(), Boolean(done))

        return res.status(200).json({task,"message":"Task created"})
    } catch (error) {
        console.log(error)
        
        return res.status(500).json({"message":"Internal Server Error"})
    }

})


app.put("/tasks/:id",async (_req, res) => {
    try {
        const id = Number(_req.params.id)
        const { title, done } = _req.body

        if(
          !Number.isInteger(id) ||
          typeof title !== "string" ||
          title.trim() === "" ||
          typeof done !== "boolean"){
                return res.status(400).json({error:"Invalid task data"})
          }

          const task = await updateTask(title.trim(), done, id)

          if(!task){
            return res.status(400).json({"message":"Task not found"})
          }

          return res.status(200).json(task)

    } catch (error) {
        console.log(error)
        return res.status(500).json({error:"Internal Server error"})
    }
});


app.delete("/tasks/:id",async (_req, res) => {
   try {
     const id = Number(_req.params.id);
     
        if (!Number.isInteger(id)) {
       return res.status(400).json({
         error: "Invalid task id",
       });
     }
 
     const deleted = await deleteTask(id);
 
     if(!deleted){
         return res.status(404).json({
         error: "Task not found",
       });
     }
 
     return res.status(204).send()
   } catch (error) {
    console.log(error)
     return res.status(500).json({error:"Internal Server error"})
    
   }
});


app.get("/tasks/:id",async (_req, res) => {
   try {
     const id = Number(_req.params.id);
 
       if (!Number.isInteger(id)) {
        return res.status(400).json({
          error: "Invalid task id",
        });
      }
 
      const taskById = await getTaskById(id);
 
      if(!taskById){
         return res.status(404).json({error:"Task not found"})
      }
 
      return res.status(200).json(taskById)
   } catch (error) {
    console.log(error)
     return res.status(500).json({error:"Internal Server error"})
   }
})

const PORT = process.env.PORT
 app.listen(PORT,()=>{
      
      console.log(`Server running on http://localhost:${PORT}`);
 })

