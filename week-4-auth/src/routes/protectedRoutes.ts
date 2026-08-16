import express from 'express'
import {authMiddleware} from '../middleware/authMiddleware.ts'

const router = express.Router()

const protectedRoute = router.post('/profile',authMiddleware,async (req, res)=>{
  res.status(200).json({message:"oken format received. Verification next."})
})

router.get('/profile',authMiddleware,(req:any, res)=>{
  const user = req.user;
  res.status(200).json({
    id:user.id,
    email:user.email,
    created_at:user.created_at
  })
})

router.get("/dashboard", authMiddleware, (req:any, res) => {
  res.status(200).json({
    message: "Welcome to your dashboard",
    user_id: req.user.id
  });
});

export default router