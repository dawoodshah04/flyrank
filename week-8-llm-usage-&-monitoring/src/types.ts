import { z } from 'zod';

// ── Plan & Tenant ──────────────────────────────────────────

export interface Plan {
  id: string;
  name: 'free' | 'pro';
  display_name: string;
  api_call_limit: number;
  ai_token_limit: number;
  price_cents: number; // integer cents, never floats
  created_at: Date;
}

export interface Tenant {
  id: string;
  name: string;
  email: string | null;
  stripe_customer_id: string | null;
  created_at: Date;
}

export interface Subscription {
  id: string;
  tenant_id: string;
  plan_id: string;
  stripe_subscription_id: string | null;
  status: 'active' | 'canceled' | 'past_due' | 'unpaid';
  current_period_start: Date | null;
  current_period_end: Date | null;
  created_at: Date;
  updated_at: Date;
}

export type UsageType = 'api_call' | 'ai_tokens';

export interface UsageEvent {
  id: string;
  tenant_id: string;
  usage_type: UsageType;
  quantity: number;
  input_tokens: number;
  cached_input_tokens: number;
  output_tokens: number;
  reasoning_tokens: number;
  idempotency_key: string;
  cost_cents: number;
  created_at: Date;
}

export interface UsageRollup {
  used: number;
  limit: number;
  remaining: number;
  cost_cents: number;
}

export interface WebhookEvent {
  id: string;
  stripe_event_id: string;
  event_type: string;
  processed_at: Date;
}

// ── Zod Schemas (validation + type inference) ──────────────

export const GenerateApiCallSchema = z.object({
  type: z.literal('api_call'),
});

export const GenerateAiTokensSchema = z.object({
  type: z.literal('ai_tokens'),
  input_tokens: z.number().int().min(0).default(0),
  cached_input_tokens: z.number().int().min(0).default(0),
  output_tokens: z.number().int().min(0).default(0),
  reasoning_tokens: z.number().int().min(0).default(0),
});

export const GenerateRequestSchema = z.discriminatedUnion('type', [
  GenerateApiCallSchema,
  GenerateAiTokensSchema,
]);

export type GenerateRequest = z.infer<typeof GenerateRequestSchema>;

export const CreateTenantSchema = z.object({
  name: z.string().min(1).max(255),
  email: z.string().email().optional(),
});

export type CreateTenantRequest = z.infer<typeof CreateTenantSchema>;
