import fs from 'fs';
import path from 'path';
import pool from './db';

async function migrate() {
  // Track applied migrations
  await pool.query(`
    CREATE TABLE IF NOT EXISTS _migrations (
      name VARCHAR(255) PRIMARY KEY,
      applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `);

  const migrationsDir = path.join(__dirname, '..', 'migrations');
  const files = fs.readdirSync(migrationsDir).filter(f => f.endsWith('.sql')).sort();

  for (const file of files) {
    const { rowCount } = await pool.query('SELECT 1 FROM _migrations WHERE name = $1', [file]);
    if (rowCount && rowCount > 0) {
      console.log(`⏭  ${file} (already applied)`);
      continue;
    }

    const sql = fs.readFileSync(path.join(migrationsDir, file), 'utf-8');
    await pool.query('BEGIN');
    try {
      await pool.query(sql);
      await pool.query('INSERT INTO _migrations (name) VALUES ($1)', [file]);
      await pool.query('COMMIT');
      console.log(`✅ ${file}`);
    } catch (err) {
      await pool.query('ROLLBACK');
      console.error(`❌ ${file}:`, err);
      process.exit(1);
    }
  }

  console.log('Migrations complete.');
  await pool.end();
}

migrate();
