-- 001: Create all tables in one migration (small project, no need to split)

-- Plans: Free + Pro
CREATE TABLE plans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(50) NOT NULL UNIQUE,
    display_name    VARCHAR(100) NOT NULL,
    api_call_limit  INTEGER NOT NULL,
    ai_token_limit  INTEGER NOT NULL,
    price_cents     INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tenants (customers)
CREATE TABLE tenants (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(255) NOT NULL,
    email               VARCHAR(255) UNIQUE,
    stripe_customer_id  VARCHAR(255) UNIQUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Subscriptions: tenant <-> plan, synced from Stripe
CREATE TABLE subscriptions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    plan_id                 UUID NOT NULL REFERENCES plans(id),
    stripe_subscription_id  VARCHAR(255) UNIQUE,
    status                  VARCHAR(50) NOT NULL DEFAULT 'active',
    current_period_start    TIMESTAMPTZ DEFAULT NOW(),
    current_period_end      TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '30 days'),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_subscriptions_tenant ON subscriptions(tenant_id);

-- Usage events: the metering heart
CREATE TABLE usage_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id),
    usage_type          VARCHAR(50) NOT NULL,
    quantity            INTEGER NOT NULL,
    input_tokens        INTEGER NOT NULL DEFAULT 0,
    cached_input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens       INTEGER NOT NULL DEFAULT 0,
    reasoning_tokens    INTEGER NOT NULL DEFAULT 0,
    idempotency_key     VARCHAR(255) NOT NULL,
    cost_cents          INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- THE critical constraint: exactly-once metering
    CONSTRAINT uq_idempotency_key UNIQUE (idempotency_key)
);
CREATE INDEX idx_usage_tenant_period ON usage_events(tenant_id, usage_type, created_at);

-- Webhook events: Stripe deduplication
CREATE TABLE webhook_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_event_id VARCHAR(255) NOT NULL UNIQUE,
    event_type      VARCHAR(255) NOT NULL,
    processed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
