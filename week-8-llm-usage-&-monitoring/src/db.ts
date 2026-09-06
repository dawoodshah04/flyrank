import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://metering:metering_dev@localhost:5432/metering_billing',
});

export default pool;
