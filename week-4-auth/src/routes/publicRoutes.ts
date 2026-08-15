import express from 'express'

const router = express.Router();

router.get('/info',(req, res)=>{
    res.status(200).json({message:"Welcome User!"})
})


export default router
