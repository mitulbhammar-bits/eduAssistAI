"""Strict output checks, transparent quality heuristics and promotion policy."""
import json
from statistics import mean


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError('Non-standard JSON constant: ' + value)


def json_checks(text):
    """Return separate (valid JSON, exact assignment schema) indicators."""
    try:
        obj = json.loads(text, object_pairs_hook=_unique_object,
                         parse_constant=_invalid_constant)
    except (ValueError, TypeError):
        return 0, 0
    valid = (isinstance(obj, dict)
             and set(obj) == {'answer', 'confidence', 'key_points'}
             and isinstance(obj['answer'], str) and bool(obj['answer'].strip())
             and obj['confidence'] in ['high', 'medium', 'low']
             and isinstance(obj['key_points'], list) and bool(obj['key_points'])
             and all(isinstance(x, str) and bool(x.strip()) for x in obj['key_points']))
    return 1, int(valid)


def quality_score(text, expected_concepts):
    """Fraction of reference concepts mentioned; a proxy, not a correctness judge."""
    lower = text.lower()
    matches = [any(term.lower() in lower for term in alternatives)
               for alternatives in expected_concepts]
    return sum(matches) / len(matches)


def summarize(version, rows):
    successful = [row for row in rows if row['response_status'] == 'success']
    def avg(key):
        values = [row[key] for row in successful if row.get(key) is not None]
        return mean(values) if values else 0.0
    return {'prompt_version': version, 'request_count': len(rows),
            'success_count': len(successful),
            'avg_latency_seconds': avg('latency_seconds'),
            'avg_input_tokens': avg('input_tokens'),
            'avg_output_tokens': avg('output_tokens'),
            'avg_cost_per_request': avg('total_cost_usd'),
            'projected_monthly_cost_usd': avg('total_cost_usd') * 10_000,
            'valid_json': sum(row['valid_json'] for row in rows) / len(rows),
            'schema_valid_rate': sum(row['schema_valid'] for row in rows) / len(rows),
            'quality_score': avg('quality_score')}


def choose_prompt(summaries):
    """Require complete, valid responses; then prefer quality, cost and latency."""
    eligible = [s for s in summaries if s['request_count'] == 5
                and s['success_count'] == 5 and s['valid_json'] == 1.0
                and s['schema_valid_rate'] == 1.0 and s['quality_score'] >= 0.8]
    if not eligible:
        return None
    eligible.sort(key=lambda s: (-s['quality_score'], s['avg_cost_per_request'],
                                s['avg_latency_seconds'], s['prompt_version']))
    return eligible[0]['prompt_version']
