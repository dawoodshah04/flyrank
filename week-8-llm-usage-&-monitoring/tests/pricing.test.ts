import { calculateTokenCost, calculateApiCallCost, PRICING } from '../src/pricing';

describe('Cost Calculation', () => {
  test('API call cost: 1 call = ceil(0.1) = 1 cent', () => {
    expect(calculateApiCallCost(1)).toBe(1);
  });

  test('API call cost: 10 calls = ceil(1.0) = 1 cent', () => {
    expect(calculateApiCallCost(10)).toBe(1);
  });

  test('API call cost: 100 calls = ceil(10.0) = 10 cents', () => {
    expect(calculateApiCallCost(100)).toBe(10);
  });

  test('token cost: each category priced separately', () => {
    // 1M input = $0.075 = 7.5 cents → 8 cents (ceil)
    expect(calculateTokenCost(1_000_000, 0, 0, 0)).toBe(8);

    // 1M cached input = $0.01875 = 1.875 cents → 2 cents (ceil)
    expect(calculateTokenCost(0, 1_000_000, 0, 0)).toBe(2);

    // 1M output = $0.30 = 30 cents
    expect(calculateTokenCost(0, 0, 1_000_000, 0)).toBe(30);

    // 1M reasoning = $0.30 = 30 cents (same as output)
    expect(calculateTokenCost(0, 0, 0, 1_000_000)).toBe(30);
  });

  test('token cost: mixed categories NOT added before pricing', () => {
    // 500k input + 200k cached + 300k output + 100k reasoning
    // = (500k × 0.075/1M) + (200k × 0.01875/1M) + (300k × 0.30/1M) + (100k × 0.30/1M)
    // = 0.0375 + 0.00375 + 0.09 + 0.03
    // = $0.16125 = 16.125 cents → 17 cents (ceil)
    expect(calculateTokenCost(500_000, 200_000, 300_000, 100_000)).toBe(17);
  });

  test('token cost: cached tokens are 75% cheaper than input', () => {
    const inputCost = calculateTokenCost(1_000_000, 0, 0, 0);
    const cachedCost = calculateTokenCost(0, 1_000_000, 0, 0);
    // cached rate / input rate = 0.01875 / 0.075 = 0.25 (75% cheaper)
    expect(PRICING.ai_tokens.cached_input_per_million / PRICING.ai_tokens.input_per_million).toBeCloseTo(0.25);
  });

  test('token cost: reasoning tokens billed at output rate', () => {
    expect(PRICING.ai_tokens.reasoning_per_million).toBe(PRICING.ai_tokens.output_per_million);
    // Same quantity → same cost
    expect(calculateTokenCost(0, 0, 500_000, 0)).toBe(calculateTokenCost(0, 0, 0, 500_000));
  });

  test('token cost: zero tokens = zero cost', () => {
    expect(calculateTokenCost(0, 0, 0, 0)).toBe(0);
  });
});
