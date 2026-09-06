// Pricing constants — pinned, auditable, referenced by EVIDENCE.md
// Rates in micro-dollars per token (multiply by qty, then convert to cents)
// Source: Gemini API pricing tiers

export const PRICING = {
  // Per-token rates in micro-dollars (1 micro-dollar = $0.000001)
  ai_tokens: {
    input_per_million: 0.075,           // $0.075 / 1M tokens
    cached_input_per_million: 0.01875,  // $0.01875 / 1M tokens (75% cheaper)
    output_per_million: 0.30,           // $0.30 / 1M tokens
    reasoning_per_million: 0.30,        // $0.30 / 1M tokens (billed as output)
  },
  // Per API call rate
  api_call: {
    per_call_cents: 0.1, // $0.001 per call = 0.1 cents
  },
} as const;

export const PLANS = {
  free: {
    name: 'free' as const,
    display_name: 'Free',
    api_call_limit: 1_000,
    ai_token_limit: 100_000,
    price_cents: 0,
  },
  pro: {
    name: 'pro' as const,
    display_name: 'Pro',
    api_call_limit: 50_000,
    ai_token_limit: 5_000_000,
    price_cents: 4_900, // $49.00
  },
} as const;

/**
 * Calculate cost in cents for a set of AI tokens.
 * Each category priced separately — never added together before pricing.
 * Returns integer cents (rounded up — never undercharge).
 */
export function calculateTokenCost(
  inputTokens: number,
  cachedInputTokens: number,
  outputTokens: number,
  reasoningTokens: number,
): number {
  const r = PRICING.ai_tokens;
  const totalDollars =
    (inputTokens * r.input_per_million) / 1_000_000 +
    (cachedInputTokens * r.cached_input_per_million) / 1_000_000 +
    (outputTokens * r.output_per_million) / 1_000_000 +
    (reasoningTokens * r.reasoning_per_million) / 1_000_000;

  // Convert to cents, round up (never undercharge)
  return Math.ceil(totalDollars * 100);
}

/**
 * Calculate cost in cents for API calls.
 */
export function calculateApiCallCost(callCount: number): number {
  return Math.ceil(callCount * PRICING.api_call.per_call_cents);
}
