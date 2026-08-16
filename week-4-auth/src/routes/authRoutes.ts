import express, { Request, Response } from 'express';
import { supabase } from '../lib/supabaseClient.js';
import { authMiddleware } from '../middleware/authMiddleware.js';

const router = express.Router();

// POST /auth/signup
router.post('/signup', async (req: Request, res: Response) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    const { data, error } = await supabase.auth.signUp({ email, password });

    if (error) {
      return res.status(400).json({ error: error.message });
    }

    return res.status(201).json({ user: data.user });
  } catch (err: any) {
    return res.status(500).json({ error: err.message || 'Internal server error' });
  }
});

// POST /auth/login
router.post('/login', async (req: Request, res: Response) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    const { data, error } = await supabase.auth.signInWithPassword({ email, password });

    if (error || !data.session) {
      return res.status(401).json({ error: 'Invalid login credentials' });
    }

    return res.status(200).json({
      access_token: data.session.access_token,
      refresh_token: data.session.refresh_token
    });
  } catch (err: any) {
    return res.status(500).json({ error: err.message || 'Internal server error' });
  }
});

// POST /auth/logout
router.post('/logout', authMiddleware, async (_req: Request, res: Response) => {
  try {
    const { error } = await supabase.auth.signOut();

    if (error) {
      return res.status(400).json({ error: error.message });
    }

    return res.status(204).send();
  } catch (err: any) {
    return res.status(500).json({ error: err.message || 'Internal server error' });
  }
});

// POST /auth/refresh (Stretch Goal)
router.post('/refresh', async (req: Request, res: Response) => {
  try {
    const { refresh_token } = req.body;

    if (!refresh_token) {
      return res.status(400).json({ error: 'Refresh token is required' });
    }

    const { data, error } = await supabase.auth.refreshSession({ refresh_token });

    if (error || !data.session) {
      return res.status(401).json({ error: 'Invalid or expired refresh token' });
    }

    return res.status(200).json({
      access_token: data.session.access_token,
      refresh_token: data.session.refresh_token
    });
  } catch (err: any) {
    return res.status(500).json({ error: err.message || 'Internal server error' });
  }
});

export default router;
