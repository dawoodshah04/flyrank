import express from 'express';
import cors from 'cors';
import 'dotenv/config';
import swaggerUi from 'swagger-ui-express';
import morgan from 'morgan';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import authRoutes from './routes/authRoutes.js';
import publicRoutes from './routes/publicRoutes.js';
import protectedRoutes from './routes/protectedRoutes.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const openapiPath = path.join(__dirname, 'docs', 'openapi.json');
const openapiDocument = JSON.parse(fs.readFileSync(openapiPath, 'utf8'));

const PORT = process.env.PORT || 3000;
const app = express();

app.use(morgan(':method :url :status :res[content-length] - :response-time ms'));
app.use(cors());
app.use(express.json());

// Serve Swagger UI
app.use('/docs', swaggerUi.serve, swaggerUi.setup(openapiDocument));

// Mount Routes
app.use('/auth', authRoutes);
app.use('/public', publicRoutes);
app.use('/protected', protectedRoutes);

app.get('/', (_req, res) => {
  res.status(200).json({
    message: 'FlyRank Auth API is running',
    docs: '/docs'
  });
});

app.listen(PORT, () => {
  console.log(`Server running and connected to Supabase`);
  console.log(`Server is listening on http://localhost:${PORT}`);
  console.log(`Swagger UI available at http://localhost:${PORT}/docs`);
});
