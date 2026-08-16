import express, { Request, Response } from 'express';

const router = express.Router();

// GET /public/info
router.get('/info', (_req: Request, res: Response) => {
  res.status(200).json({ message: 'Welcome stranger! This info is public.' });
});

export default router;
