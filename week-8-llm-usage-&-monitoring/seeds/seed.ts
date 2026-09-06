import pool from '../src/db';
import { PLANS } from '../src/pricing';

async function seed() {
  // Upsert plans
  for (const plan of Object.values(PLANS)) {
    await pool.query(
      `INSERT INTO plans (name, display_name, api_call_limit, ai_token_limit, price_cents)
       VALUES ($1, $2, $3, $4, $5)
       ON CONFLICT (name) DO UPDATE SET
         display_name = EXCLUDED.display_name,
         api_call_limit = EXCLUDED.api_call_limit,
         ai_token_limit = EXCLUDED.ai_token_limit,
         price_cents = EXCLUDED.price_cents`,
      [plan.name, plan.display_name, plan.api_call_limit, plan.ai_token_limit, plan.price_cents]
    );
    console.log(`✅ Plan: ${plan.display_name}`);
  }

  // Create demo tenants with Free plan
  const { rows: [freePlan] } = await pool.query(`SELECT id FROM plans WHERE name = 'free'`);

  const tenants = [
    { name: 'Acme Corp', email: 'admin@acme.example.com' },
    { name: 'Globex Inc', email: 'admin@globex.example.com' },
  ];

  for (const t of tenants) {
    const { rows: [tenant] } = await pool.query(
      `INSERT INTO tenants (name, email) VALUES ($1, $2)
       ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name
       RETURNING id`,
      [t.name, t.email]
    );

    await pool.query(
      `INSERT INTO subscriptions (tenant_id, plan_id, status)
       VALUES ($1, $2, 'active')
       ON CONFLICT DO NOTHING`,
      [tenant.id, freePlan.id]
    );
    console.log(`✅ Tenant: ${t.name} (${tenant.id})`);
  }

  console.log('Seed complete.');
  await pool.end();
}

seed();
