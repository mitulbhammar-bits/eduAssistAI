"""Small file helpers shared by the experiment and notebook."""
import csv
import json
from pathlib import Path

REQUEST_COLUMNS = ['question_id', 'prompt_version', 'registry_version', 'model',
    'model_returned', 'start_time_utc', 'end_time_utc', 'latency_seconds',
    'response_status', 'http_status', 'finish_reason', 'input_tokens', 'output_tokens',
    'total_tokens', 'prompt_eval_seconds', 'generation_seconds',
    'input_price_per_million_usd', 'output_price_per_million_usd',
    'input_cost_usd', 'output_cost_usd', 'total_cost_usd', 'actual_external_cost_usd',
    'valid_json', 'schema_valid', 'quality_score', 'error_type', 'response_text']
SUMMARY_COLUMNS = ['prompt_version', 'request_count', 'success_count',
    'avg_latency_seconds', 'avg_input_tokens', 'avg_output_tokens',
    'avg_cost_per_request', 'projected_monthly_cost_usd', 'valid_json',
    'schema_valid_rate', 'quality_score', 'recommended']


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def save_csv(path, rows, columns):
    with Path(path).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def load_rows(path):
    with Path(path).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))
