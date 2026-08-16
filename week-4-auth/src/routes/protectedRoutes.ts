import express, { Request, Response } from 'express';
import { authMiddleware } from '../middleware/authMiddleware.js';

const router = express.Router();

// GET /protected/profile
router.get('/profile', authMiddleware, (req: Request, res: Response) => {
  const user = req.user;
  if (!user) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }

  return res.status(200).json({
    id: user.id,
    email: user.email,
    created_at: user.created_at
  });
});

// GET /protected/dashboard (Stage 4 checkpoint route)
router.get('/dashboard', authMiddleware, (req: Request, res: Response) => {
  const user = req.user;
  return res.status(200).json({
    message: 'Welcome to your dashboard',
    user_id: user?.id
  });
});

// GET /protected/admin (Stretch Goal: 403 Forbidden demonstration)
router.get('/admin', authMiddleware, (req: Request, res: Response) => {
  const user = req.user;
  const isAdmin = user?.app_metadata?.role === 'admin' || user?.user_metadata?.role === 'admin';

  if (!isAdmin) {
    return res.status(403).json({
      error: 'Forbidden: Admin access required',
      message: 'Authentication succeeded, but you do not have permission to access this resource.'
    });
  }

  return res.status(200).json({
    message: 'Welcome Admin! You have access to secret data.'
  });
});

export default router;