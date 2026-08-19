import type { Request, Response, NextFunction } from 'express';
import { supabase } from '../lib/supabaseClient.js';

export async function authMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  const authHeader = req.get('Authorization');

if (!authHeader?.startsWith('Bearer ')) {
  res.status(401).json({
    error: 'Access token required',
  });
  return;
}

const token = authHeader.slice('Bearer '.length).trim();

if (!token) {
  res.status(401).json({
    error: 'Access token required',
  });
  return;
}

const { data, error } = await supabase.auth.getUser(token);

if (error || !data.user) {
  res.status(401).json({
    error: 'Invalid or expired token',
  });
  return;
}

req.user = data.user;
next();
}