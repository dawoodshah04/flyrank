import express from 'express'
import {authMiddleware} from '../middleware/authMiddleware.js'

const router = express.Router()

const protectedRoute = router.post('/profile',authMiddleware,async (req, res)=>{
  res.status(200).json({message:"oken format received. Verification next."})
})

export default router