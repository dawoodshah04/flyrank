import express from 'express';
import cors from 'cors';
import 'dotenv/config';
import swaggerUi from 'swagger-ui-express';
import morgan from 'morgan';
import authRoutes from './routes/authRoutes.ts';
import publicRoutes from './routes/publicRoutes.ts';
import protectedRoutes from './routes/protectedRoutes.ts';

const PORT = process.env.PORT;
const app = express();
app.use(morgan(':method :url :status :res[content-length] - :response-time ms'));
app.use(cors());
app.use(express.json());

app.use('/auth',authRoutes);
app.use('/public',publicRoutes);
app.use('/protected',protectedRoutes);

app.get('/',async (_req, res)=>{
    res.status(200).json({"message":"health ok"});
})

app.listen(PORT,()=>{
    console.log(`Server is listening on PORT:${PORT}`);
})
