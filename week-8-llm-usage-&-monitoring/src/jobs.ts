import cron from 'node-cron';
import pool from './db';

// Background job: check usage thresholds every 5 minutes
// Logs alerts at 80% and 100% — satisfies "≥1 background job" requirement
export function startUsageAlertJob() {
  cron.schedule('*/5 * * * *', async () => {
    try {
      const { rows } = await pool.query(`
        SELECT t.id as tenant_id, t.name as tenant_name,
               p.name as plan_name, p.api_call_limit, p.ai_token_limit,
               COALESCE(api.used, 0) as api_used,
               COALESCE(tok.used, 0) as tokens_used
        FROM tenants t
        JOIN subscriptions s ON s.tenant_id = t.id AND s.status = 'active'
        JOIN plans p ON s.plan_id = p.id
        LEFT JOIN (
          SELECT tenant_id, SUM(quantity)::int as used
          FROM usage_events WHERE usage_type = 'api_call' AND created_at >= date_trunc('month', NOW())
          GROUP BY tenant_id
        ) api ON api.tenant_id = t.id
        LEFT JOIN (
          SELECT tenant_id, SUM(quantity)::int as used
          FROM usage_events WHERE usage_type = 'ai_tokens' AND created_at >= date_trunc('month', NOW())
          GROUP BY tenant_id
        ) tok ON tok.tenant_id = t.id
      `);

      for (const row of rows) {
        const apiPct = row.api_call_limit > 0 ? (row.api_used / row.api_call_limit) * 100 : 0;
        const tokPct = row.ai_token_limit > 0 ? (row.tokens_used / row.ai_token_limit) * 100 : 0;

        if (apiPct >= 100) console.warn(`🚨 ${row.tenant_name}: API calls at ${apiPct.toFixed(0)}% (${row.api_used}/${row.api_call_limit})`);
        else if (apiPct >= 80) console.warn(`⚠️  ${row.tenant_name}: API calls at ${apiPct.toFixed(0)}% (${row.api_used}/${row.api_call_limit})`);

        if (tokPct >= 100) console.warn(`🚨 ${row.tenant_name}: AI tokens at ${tokPct.toFixed(0)}% (${row.tokens_used}/${row.ai_token_limit})`);
        else if (tokPct >= 80) console.warn(`⚠️  ${row.tenant_name}: AI tokens at ${tokPct.toFixed(0)}% (${row.tokens_used}/${row.ai_token_limit})`);
      }
    } catch (err) {
      console.error('Usage alert job failed:', err);
      // ponytail: logs error, no retry mechanism. Add dead-letter queue if this job becomes critical.
    }
  });

  console.log('📊 Usage alert job scheduled (every 5 min)');
}
