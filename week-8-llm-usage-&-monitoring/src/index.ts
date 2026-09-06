import 'dotenv/config';
import express, { Request, Response, NextFunction } from 'express';
import pool from './db';
import { GenerateRequestSchema, CreateTenantSchema } from './types';
import type { Plan, Subscription, UsageEvent, GenerateRequest } from './types';
import { calculateTokenCost, calculateApiCallCost, PLANS } from './pricing';
import Stripe from 'stripe';

const app = express();

// ── Stripe setup ───────────────────────────────────────────
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || '', {
  apiVersion: '2025-02-24.acacia',
});
const WEBHOOK_SECRET = process.env.STRIPE_WEBHOOK_SECRET || '';

// ── Middleware ──────────────────────────────────────────────
// Raw body for Stripe webhook verification — must come BEFORE express.json()
app.post('/api/v1/webhooks/stripe', express.raw({ type: 'application/json' }));
// JSON for everything else
app.use(express.json());

// ── Error handler ──────────────────────────────────────────
class AppError extends Error {
  constructor(public statusCode: number, message: string) {
    super(message);
  }
}

function errorHandler(err: Error, _req: Request, res: Response, _next: NextFunction) {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({ error: err.message });
  }
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
}

// ── Helper: get tenant's active subscription + plan ────────
async function getTenantPlan(tenantId: string): Promise<{ subscription: Subscription; plan: Plan }> {
  const { rows } = await pool.query(
    `SELECT s.*, p.name as plan_name, p.display_name, p.api_call_limit, p.ai_token_limit, p.price_cents
     FROM subscriptions s JOIN plans p ON s.plan_id = p.id
     WHERE s.tenant_id = $1 AND s.status = 'active'
     ORDER BY s.created_at DESC LIMIT 1`,
    [tenantId]
  );
  if (!rows[0]) throw new AppError(404, 'No active subscription found');
  const row = rows[0];
  return {
    subscription: row as Subscription,
    plan: {
      id: row.plan_id,
      name: row.plan_name,
      display_name: row.display_name,
      api_call_limit: row.api_call_limit,
      ai_token_limit: row.ai_token_limit,
      price_cents: row.price_cents,
      created_at: row.created_at,
    },
  };
}

// ── Helper: get current month usage ────────────────────────
async function getMonthlyUsage(tenantId: string, usageType: string): Promise<number> {
  const { rows } = await pool.query(
    `SELECT COALESCE(SUM(quantity), 0) as total
     FROM usage_events
     WHERE tenant_id = $1 AND usage_type = $2
       AND created_at >= date_trunc('month', NOW())`,
    [tenantId, usageType]
  );
  return parseInt(rows[0].total, 10);
}

// ── Health ──────────────────────────────────────────────────
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// ── POST /api/v1/tenants ────────────────────────────────────
app.post('/api/v1/tenants', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const parsed = CreateTenantSchema.safeParse(req.body);
    if (!parsed.success) throw new AppError(400, parsed.error.issues.map(i => i.message).join(', '));

    const { name, email } = parsed.data;
    const { rows: [tenant] } = await pool.query(
      `INSERT INTO tenants (name, email) VALUES ($1, $2) RETURNING *`,
      [name, email || null]
    );

    // Auto-assign Free plan
    const { rows: [freePlan] } = await pool.query(`SELECT id FROM plans WHERE name = 'free'`);
    await pool.query(
      `INSERT INTO subscriptions (tenant_id, plan_id, status) VALUES ($1, $2, 'active')`,
      [tenant.id, freePlan.id]
    );

    res.status(201).json(tenant);
  } catch (err) { next(err); }
});

// ── GET /api/v1/tenants/:id ─────────────────────────────────
app.get('/api/v1/tenants/:id', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { rows: [tenant] } = await pool.query('SELECT * FROM tenants WHERE id = $1', [req.params.id]);
    if (!tenant) throw new AppError(404, 'Tenant not found');

    const { plan } = await getTenantPlan(tenant.id);
    res.json({ ...tenant, plan });
  } catch (err) { next(err); }
});

// ── POST /api/v1/generate (THE billable endpoint) ──────────
app.post('/api/v1/generate', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const tenantId = req.headers['x-tenant-id'] as string;
    if (!tenantId) throw new AppError(400, 'Missing X-Tenant-Id header');

    const idempotencyKey = req.headers['idempotency-key'] as string;
    if (!idempotencyKey) throw new AppError(400, 'Missing Idempotency-Key header');

    // Check tenant exists
    const { rows: [tenant] } = await pool.query('SELECT id FROM tenants WHERE id = $1', [tenantId]);
    if (!tenant) throw new AppError(404, 'Tenant not found');

    // ── Idempotency check: return existing event if key already used ──
    const { rows: existing } = await pool.query(
      'SELECT * FROM usage_events WHERE idempotency_key = $1',
      [idempotencyKey]
    );
    if (existing.length > 0) {
      const ev = existing[0] as UsageEvent;
      const used = await getMonthlyUsage(tenantId, ev.usage_type);
      const { plan } = await getTenantPlan(tenantId);
      const limit = ev.usage_type === 'api_call' ? plan.api_call_limit : plan.ai_token_limit;
      return res.json({
        event_id: ev.id,
        usage_type: ev.usage_type,
        quantity: ev.quantity,
        cost_cents: ev.cost_cents,
        quota: { used, limit, remaining: Math.max(0, limit - used) },
        deduplicated: true,
      });
    }

    // ── Validate request body ──
    const parsed = GenerateRequestSchema.safeParse(req.body);
    if (!parsed.success) throw new AppError(400, parsed.error.issues.map(i => i.message).join(', '));

    const body = parsed.data;
    const { plan } = await getTenantPlan(tenantId);

    let usageType: string;
    let quantity: number;
    let costCents: number;
    let inputTokens = 0, cachedInputTokens = 0, outputTokens = 0, reasoningTokens = 0;

    if (body.type === 'api_call') {
      usageType = 'api_call';
      quantity = 1;
      costCents = calculateApiCallCost(1);
    } else {
      usageType = 'ai_tokens';
      inputTokens = body.input_tokens;
      cachedInputTokens = body.cached_input_tokens;
      outputTokens = body.output_tokens;
      reasoningTokens = body.reasoning_tokens;
      quantity = inputTokens + cachedInputTokens + outputTokens + reasoningTokens;
      costCents = calculateTokenCost(inputTokens, cachedInputTokens, outputTokens, reasoningTokens);
    }

    // ── Quota check ──
    const currentUsage = await getMonthlyUsage(tenantId, usageType);
    const limit = usageType === 'api_call' ? plan.api_call_limit : plan.ai_token_limit;

    if (currentUsage + quantity > limit) {
      // 429 if they have a paid plan or are on Free, 402 if Free (suggest upgrade)
      if (plan.name === 'free') {
        throw new AppError(402, JSON.stringify({
          error: 'PAYMENT_REQUIRED',
          message: `Free plan limit reached. Used ${currentUsage.toLocaleString()} of ${limit.toLocaleString()} ${usageType === 'api_call' ? 'API calls' : 'tokens'}. Upgrade to Pro for higher limits.`,
          usage: { used: currentUsage, limit },
          upgrade_url: '/api/v1/checkout',
        }));
      }
      throw new AppError(429, JSON.stringify({
        error: 'QUOTA_EXCEEDED',
        message: `${usageType === 'api_call' ? 'API call' : 'AI token'} quota exceeded. Used ${currentUsage.toLocaleString()} of ${limit.toLocaleString()}. Requested ${quantity.toLocaleString()} would exceed limit by ${(currentUsage + quantity - limit).toLocaleString()}.`,
        usage: { used: currentUsage, limit },
      }));
    }

    // ── Record usage event (ON CONFLICT for concurrent retry safety) ──
    const { rows: [event] } = await pool.query(
      `INSERT INTO usage_events (tenant_id, usage_type, quantity, input_tokens, cached_input_tokens, output_tokens, reasoning_tokens, idempotency_key, cost_cents)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
       ON CONFLICT (idempotency_key) DO NOTHING
       RETURNING *`,
      [tenantId, usageType, quantity, inputTokens, cachedInputTokens, outputTokens, reasoningTokens, idempotencyKey, costCents]
    );

    // If ON CONFLICT hit (concurrent duplicate), fetch the existing one
    const finalEvent = event || existing[0] || (await pool.query('SELECT * FROM usage_events WHERE idempotency_key = $1', [idempotencyKey])).rows[0];
    const newUsage = await getMonthlyUsage(tenantId, usageType);

    res.status(201).json({
      event_id: finalEvent.id,
      usage_type: finalEvent.usage_type,
      quantity: finalEvent.quantity,
      cost_cents: finalEvent.cost_cents,
      quota: { used: newUsage, limit, remaining: Math.max(0, limit - newUsage) },
      deduplicated: !event,
    });
  } catch (err) { next(err); }
});

// ── GET /api/v1/usage ───────────────────────────────────────
app.get('/api/v1/usage', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const tenantId = req.headers['x-tenant-id'] as string;
    if (!tenantId) throw new AppError(400, 'Missing X-Tenant-Id header');

    const { plan } = await getTenantPlan(tenantId);

    // Rollup: usage + cost per type for current month
    const { rows } = await pool.query(
      `SELECT usage_type,
              COALESCE(SUM(quantity), 0)::int as used,
              COALESCE(SUM(cost_cents), 0)::int as cost_cents,
              COALESCE(SUM(input_tokens), 0)::int as input_tokens,
              COALESCE(SUM(cached_input_tokens), 0)::int as cached_input_tokens,
              COALESCE(SUM(output_tokens), 0)::int as output_tokens,
              COALESCE(SUM(reasoning_tokens), 0)::int as reasoning_tokens
       FROM usage_events
       WHERE tenant_id = $1 AND created_at >= date_trunc('month', NOW())
       GROUP BY usage_type`,
      [tenantId]
    );

    const apiCalls = rows.find(r => r.usage_type === 'api_call');
    const aiTokens = rows.find(r => r.usage_type === 'ai_tokens');

    res.json({
      tenant_id: tenantId,
      plan: plan.name,
      period: {
        start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString(),
        end: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).toISOString(),
      },
      api_calls: {
        used: apiCalls?.used || 0,
        limit: plan.api_call_limit,
        remaining: Math.max(0, plan.api_call_limit - (apiCalls?.used || 0)),
        cost_cents: apiCalls?.cost_cents || 0,
      },
      ai_tokens: {
        used: aiTokens?.used || 0,
        limit: plan.ai_token_limit,
        remaining: Math.max(0, plan.ai_token_limit - (aiTokens?.used || 0)),
        cost_cents: aiTokens?.cost_cents || 0,
        breakdown: {
          input_tokens: aiTokens?.input_tokens || 0,
          cached_input_tokens: aiTokens?.cached_input_tokens || 0,
          output_tokens: aiTokens?.output_tokens || 0,
          reasoning_tokens: aiTokens?.reasoning_tokens || 0,
        },
      },
      total_cost_cents: (apiCalls?.cost_cents || 0) + (aiTokens?.cost_cents || 0),
    });
  } catch (err) { next(err); }
});

// ── POST /api/v1/checkout (Stripe Checkout session) ─────────
app.post('/api/v1/checkout', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const tenantId = req.headers['x-tenant-id'] as string;
    if (!tenantId) throw new AppError(400, 'Missing X-Tenant-Id header');

    const { rows: [tenant] } = await pool.query('SELECT * FROM tenants WHERE id = $1', [tenantId]);
    if (!tenant) throw new AppError(404, 'Tenant not found');

    // Create or reuse Stripe customer
    let customerId = tenant.stripe_customer_id;
    if (!customerId) {
      const customer = await stripe.customers.create({
        name: tenant.name,
        email: tenant.email || undefined,
        metadata: { tenant_id: tenantId },
      });
      customerId = customer.id;
      await pool.query('UPDATE tenants SET stripe_customer_id = $1 WHERE id = $2', [customerId, tenantId]);
    }

    // Create a Checkout session for Pro plan
    // You need to create a Price in Stripe Dashboard or via API first.
    // For simplicity, we create an ad-hoc price.
    const session = await stripe.checkout.sessions.create({
      customer: customerId,
      mode: 'subscription',
      line_items: [{
        price_data: {
          currency: 'usd',
          product_data: { name: 'Pro Plan' },
          unit_amount: PLANS.pro.price_cents,
          recurring: { interval: 'month' },
        },
        quantity: 1,
      }],
      success_url: `${req.headers.origin || 'http://localhost:3000'}/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${req.headers.origin || 'http://localhost:3000'}/checkout/cancel`,
      metadata: { tenant_id: tenantId },
    });

    res.json({ checkout_url: session.url });
  } catch (err) { next(err); }
});

// ── POST /api/v1/webhooks/stripe ────────────────────────────
app.post('/api/v1/webhooks/stripe', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const sig = req.headers['stripe-signature'] as string;
    if (!sig) throw new AppError(400, 'Missing stripe-signature header');

    let event: Stripe.Event;
    try {
      event = stripe.webhooks.constructEvent(req.body, sig, WEBHOOK_SECRET);
    } catch {
      throw new AppError(400, 'Invalid webhook signature');
    }

    // ── Deduplicate: skip if already processed ──
    const { rowCount } = await pool.query(
      `INSERT INTO webhook_events (stripe_event_id, event_type) VALUES ($1, $2)
       ON CONFLICT (stripe_event_id) DO NOTHING`,
      [event.id, event.type]
    );
    if (rowCount === 0) {
      // Already processed — idempotent, return 200
      return res.json({ received: true, deduplicated: true });
    }

    // ── Handle event types ──
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session;
        const tenantId = session.metadata?.tenant_id;
        if (!tenantId) break;

        const { rows: [proPlan] } = await pool.query(`SELECT id FROM plans WHERE name = 'pro'`);

        // Update or create subscription
        await pool.query(
          `UPDATE subscriptions SET plan_id = $1, stripe_subscription_id = $2, status = 'active', updated_at = NOW()
           WHERE tenant_id = $3`,
          [proPlan.id, session.subscription, tenantId]
        );
        console.log(`🔄 Tenant ${tenantId} upgraded to Pro via checkout`);
        break;
      }

      case 'customer.subscription.updated': {
        const sub = event.data.object as Stripe.Subscription;
        const status = sub.status === 'active' ? 'active' : sub.status === 'past_due' ? 'past_due' : 'canceled';
        await pool.query(
          `UPDATE subscriptions SET status = $1, current_period_start = to_timestamp($2), current_period_end = to_timestamp($3), updated_at = NOW()
           WHERE stripe_subscription_id = $4`,
          [status, sub.current_period_start, sub.current_period_end, sub.id]
        );
        console.log(`🔄 Subscription ${sub.id} updated to ${status}`);
        break;
      }

      case 'customer.subscription.deleted': {
        const sub = event.data.object as Stripe.Subscription;
        // Downgrade to Free
        const { rows: [freePlan] } = await pool.query(`SELECT id FROM plans WHERE name = 'free'`);
        await pool.query(
          `UPDATE subscriptions SET plan_id = $1, status = 'active', stripe_subscription_id = NULL, updated_at = NOW()
           WHERE stripe_subscription_id = $2`,
          [freePlan.id, sub.id]
        );
        console.log(`🔄 Subscription ${sub.id} deleted → downgraded to Free`);
        break;
      }
    }

    res.json({ received: true });
  } catch (err) { next(err); }
});

// ── Error handler (must be last) ────────────────────────────
app.use(errorHandler);

// ── Background job ──────────────────────────────────────────
import { startUsageAlertJob } from './jobs';

// ── Start ───────────────────────────────────────────────────
const PORT = parseInt(process.env.PORT || '3000', 10);
app.listen(PORT, () => {
  console.log(`🚀 Metering & Billing Engine running on port ${PORT}`);
  startUsageAlertJob();
});

export default app; // for testing
