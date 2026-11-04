"""Token-based hosting estimates, never real cloud charges."""
import math


def token_costs(input_tokens, output_tokens, input_rate, output_rate):
    """Rates are USD per million tokens; preserve precision until presentation."""
    if any(not math.isfinite(x) or x < 0 for x in
           (input_tokens, output_tokens, input_rate, output_rate)):
        raise ValueError('Token counts and prices must be finite and non-negative.')
    input_cost = input_tokens / 1_000_000 * input_rate
    output_cost = output_tokens / 1_000_000 * output_rate
    return {'input_cost_usd': input_cost, 'output_cost_usd': output_cost,
            'total_cost_usd': input_cost + output_cost}


def hosting_token_rates(rows, hourly_rate):
    """Pool measured phase times and counts across all prompts for fair pricing.

    Effective input rate = host USD/hour * input phase seconds / 3600
                           / total input tokens * 1,000,000.
    The output rate uses the generation phase in the same formula.
    This is a hardware-transfer estimate, not an advertised token tariff.
    """
    rates = []
    for token_key, seconds_key in [('input_tokens', 'prompt_eval_seconds'),
                                    ('output_tokens', 'generation_seconds')]:
        tokens = sum(row[token_key] for row in rows)
        seconds = sum(row[seconds_key] for row in rows)
        if tokens <= 0 or seconds < 0 or not math.isfinite(seconds):
            raise ValueError('Valid tokenizer counts and server timings are required.')
        rates.append(hourly_rate * seconds / 3600 / tokens * 1_000_000)
    return tuple(rates)
