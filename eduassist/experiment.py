"""Run three prompts on five questions and preserve the evidence behind each result."""
import difflib
import json
import platform
import statistics
from datetime import datetime, timezone
from . import tracking
from .api import call_llm
from .config import ROOT, load_settings
from .economics import hosting_token_rates, token_costs
from .evaluation import choose_prompt, json_checks, quality_score, summarize
from .files import REQUEST_COLUMNS, SUMMARY_COLUMNS, save_csv, save_json


def read_inputs():
    templates = {version: next((ROOT / 'prompts').glob(version + '_*.txt')).read_text().strip()
                 for version in ('v1', 'v2', 'v3')}
    questions = json.loads((ROOT / 'data' / 'academic_questions.json').read_text())
    if len(questions) != 5 or len({q['question_id'] for q in questions}) != 5:
        raise ValueError('Use exactly five distinct questions for this assignment.')
    return templates, questions


def assign_costs(rows, settings):
    billed = [row for row in rows if row['input_tokens'] is not None]
    if not billed:
        return {'method': 'unavailable', 'input_rate': None, 'output_rate': None}
    all_timings = all(row['prompt_eval_seconds'] is not None
                      and row['generation_seconds'] is not None for row in billed)
    hourly = settings['hosting']['usd_per_hour']
    if all_timings:
        input_rate, output_rate = hosting_token_rates(billed, hourly)
        method = 'pooled_server_phase_time_hosting_estimate'
    else:
        seconds = sum(row['latency_seconds'] for row in billed)
        tokens = sum(row['total_tokens'] for row in billed)
        if tokens <= 0:
            raise ValueError('No usable tokenizer counts; cost cannot be estimated.')
        input_rate = output_rate = hourly * seconds / 3600 / tokens * 1_000_000
        method = 'pooled_wall_clock_hosting_estimate'
    for row in rows:
        row['input_price_per_million_usd'] = input_rate
        row['output_price_per_million_usd'] = output_rate
        row['actual_external_cost_usd'] = 0.0
        if row['input_tokens'] is not None:
            row.update(token_costs(row['input_tokens'], row['output_tokens'], input_rate, output_rate))
    return {'method': method, 'input_rate': input_rate, 'output_rate': output_rate,
            'usd_per_hour': hourly, 'currency': 'USD',
            'interpretation': 'Estimated hosting cost; not a provider token price or invoice.'}


def latency_summary(rows):
    result = []
    for version in ('v1', 'v2', 'v3'):
        values = [r['latency_seconds'] for r in rows
                  if r['prompt_version'] == version and r['response_status'] == 'success']
        if values:
            result.append({'prompt_version': version, 'count': len(values),
                'mean': statistics.mean(values), 'median': statistics.median(values),
                'minimum': min(values), 'maximum': max(values),
                'sample_standard_deviation': statistics.stdev(values) if len(values) > 1 else 0.0})
    return result


def save_prompt_diffs(templates):
    chunks = []
    for earlier, later in [('v1', 'v2'), ('v2', 'v3')]:
        chunks.extend(difflib.unified_diff(templates[earlier].splitlines(True),
            templates[later].splitlines(True), fromfile=earlier, tofile=later))
        chunks.append('\n')
    (ROOT / 'reports' / 'prompt_comparison.diff').write_text(''.join(chunks))


def run_experiment(settings_path=None):
    settings = load_settings(settings_path)
    templates, questions = read_inputs()
    # Import/setup MLflow before making any inference requests; missing dependencies fail early.
    registry = tracking.register_prompts(templates)
    batch = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    evidence_dir = ROOT / 'evidence' / batch
    evidence_dir.mkdir(parents=True)
    rows = []
    schedule = []
    for index, question in enumerate(questions):
        versions = ['v1', 'v2', 'v3']
        versions = versions[index % 3:] + versions[:index % 3]
        for version in versions:
            schedule.append((question, version))
    for question, version in schedule:
        prompt = templates[version].replace('{{question}}', question['question'])
        measured, raw = call_llm(prompt, settings)
        valid, schema = json_checks(measured['response_text'])
        if measured['response_status'] != 'success':
            valid, schema = 0, 0
        row = dict(measured, question_id=question['question_id'], prompt_version=version,
                   registry_version=registry[version]['version'], model=settings['model'],
                   valid_json=valid, schema_valid=schema,
                   quality_score=quality_score(measured['response_text'], question['expected_concepts']))
        rows.append(row)
        save_json(evidence_dir / f"{version}_{question['question_id']}.json",
                  {'question': question, 'prompt': prompt, 'measurement': row, 'api_response': raw})
        save_csv(evidence_dir / 'requests_in_progress.csv', rows, REQUEST_COLUMNS)
        print(f"{version} {question['question_id']}: {row['response_status']}, "
              f"{row['latency_seconds']:.3f}s, JSON={valid}, schema={schema}", flush=True)
    pricing = assign_costs(rows, settings)
    summaries = [summarize(version, [r for r in rows if r['prompt_version'] == version])
                 for version in ('v1', 'v2', 'v3')]
    selected = choose_prompt(summaries)
    for summary in summaries:
        summary['recommended'] = 'Yes' if summary['prompt_version'] == selected else 'No'
    save_csv(ROOT / 'latency_tokens_cost.csv', rows, REQUEST_COLUMNS)
    save_csv(ROOT / 'prompt_evaluation_results.csv', summaries, SUMMARY_COLUMNS)
    save_csv(ROOT / 'reports' / 'human_review.csv',
             [{'question_id': r['question_id'], 'prompt_version': r['prompt_version']}
              for r in rows],
             ['question_id', 'prompt_version', 'accurate', 'clear', 'complete', 'reviewer_notes'])
    save_csv(ROOT / 'reports' / 'task1_latency_table.csv',
             [r for r in rows if r['prompt_version'] == 'v1'], REQUEST_COLUMNS)
    stats = latency_summary(rows)
    if stats:
        save_csv(ROOT / 'reports' / 'latency_summary.csv', stats, list(stats[0]))
    save_prompt_diffs(templates)
    metadata = {'batch_id': batch, 'evidence_type': 'real_local_model_execution',
        'settings': settings, 'effective_pricing': pricing, 'python': platform.python_version(),
        'platform': platform.platform(), 'production_candidate': selected,
        'actual_external_inference_spend_usd': 0.0,
        'request_order': [f"{v}/{q['question_id']}" for q, v in schedule],
        'notes': ['No grammar/JSON mode is applied; only prompt wording differs.',
                  'Temperature zero and seed do not guarantee bitwise determinism.',
                  'No retries or warmups; first-call initialization can affect latency.',
                  'Prompt cache disabled where supported; check server settings.',
                  'Five questions are a small sample; quality_score is a concept-match proxy.']}
    save_json(ROOT / 'reports' / 'run_metadata.json', metadata)
    files = [ROOT / 'latency_tokens_cost.csv', ROOT / 'prompt_evaluation_results.csv',
             ROOT / 'reports' / 'prompt_comparison.diff', ROOT / 'reports' / 'run_metadata.json']
    run_ids = tracking.log_results(summaries, registry, settings, batch, files)
    # A fresh batch invalidates any previous production evidence in the reports folder.
    promotion = {'verified': False, 'reason': 'No candidate meets every promotion gate.'}
    if selected:
        promotion = tracking.promote(selected, registry)
    metadata['run_ids'] = run_ids
    save_json(ROOT / 'reports' / 'run_metadata.json', metadata)
    save_json(ROOT / 'reports' / 'production_alias.json', promotion)
    # Archive the final derived files so reruns do not erase the original measurements.
    import shutil
    for path in files + [ROOT / 'reports' / 'production_alias.json',
                         ROOT / 'reports' / 'prompt_registry.json']:
        shutil.copy2(path, evidence_dir / path.name)
    print('Production:', selected or 'not promoted (inspect failed checks)')
    return rows, summaries, metadata
