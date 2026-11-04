"""Check real evidence. A starter deliberately fails final-submission readiness."""
import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eduassist.config import ROOT
from eduassist.files import load_rows, save_json
from eduassist.reporting import word_count

SCREENSHOTS = ['01_experiment.png', '02_prompt_registry.png', '03_metrics.png',
               '04_prompt_diff.png', '05_production_alias.png']


def verify():
    pending = []
    def require(condition, message):
        if not condition:
            pending.append(message)
    required = ['README.md', 'requirements.txt', 'settings.json', 'eduassist_assignment.ipynb',
                'eduassist_assignment.html', 'latency_tokens_cost.csv',
                'prompt_evaluation_results.csv', 'reports/assignment_report.pdf',
                'reports/assignment_report.md', 'reports/promotion_justification.txt', 'reports/run_metadata.json',
                'reports/prompt_registry.json', 'reports/production_alias.json', 'mlflow.db']
    for relative in required:
        require((ROOT / relative).is_file(), 'Missing: ' + relative)
    try:
        requests = load_rows(ROOT / 'latency_tokens_cost.csv')
        summaries = load_rows(ROOT / 'prompt_evaluation_results.csv')
        expected = {(f'Q{i}', v) for i in range(1, 6) for v in ('v1', 'v2', 'v3')}
        pairs = [(r['question_id'], r['prompt_version']) for r in requests]
        require(len(pairs) == 15 and set(pairs) == expected, 'Need exactly 15 real requests, one per version/question.')
        require(bool(requests) and all(r['response_status'] == 'success' for r in requests),
                'Every request must complete successfully; inspect errors/truncations.')
        require(len(summaries) == 3 and {s['prompt_version'] for s in summaries} == {'v1','v2','v3'},
                'Need all three measured prompt summaries.')
        for row in requests:
            label = row['prompt_version'] + '/' + row['question_id']
            i, o, t = (int(row[k]) for k in ('input_tokens','output_tokens','total_tokens'))
            require(i >= 0 and o >= 0 and i + o == t, 'Invalid tokenizer usage: ' + label)
            input_cost = i / 1e6 * float(row['input_price_per_million_usd'])
            output_cost = o / 1e6 * float(row['output_price_per_million_usd'])
            require(math.isclose(float(row['input_cost_usd']), input_cost, abs_tol=1e-12), 'Input cost mismatch: ' + label)
            require(math.isclose(float(row['output_cost_usd']), output_cost, abs_tol=1e-12), 'Output cost mismatch: ' + label)
            require(math.isclose(float(row['total_cost_usd']), input_cost + output_cost, abs_tol=1e-12),
                    'Total cost mismatch: ' + label)
        for summary in summaries:
            require(math.isclose(float(summary['projected_monthly_cost_usd']),
                float(summary['avg_cost_per_request']) * 10_000, abs_tol=1e-10), 'Monthly projection mismatch.')
    except (ValueError, KeyError, OSError) as error:
        pending.append('Request/summary tables are incomplete or invalid: ' + type(error).__name__)
    try:
        notebook = json.loads((ROOT / 'eduassist_assignment.ipynb').read_text())
        code = [c for c in notebook['cells'] if c['cell_type'] == 'code']
        require(all(c.get('execution_count') is not None for c in code), 'Notebook needs actual execution before submission.')
        require(not any(o.get('output_type') == 'error' for c in code for o in c.get('outputs', [])),
                'Notebook contains execution errors.')
        export = (ROOT / 'eduassist_assignment.html').read_text()
        require('UNEXECUTED STARTER' not in export, 'Replace source-only HTML with the executed notebook export.')
    except (ValueError, KeyError, OSError):
        pending.append('Notebook/export missing or invalid.')
    try:
        alias = json.loads((ROOT / 'reports/production_alias.json').read_text())
        metadata = json.loads((ROOT / 'reports/run_metadata.json').read_text())
        require(alias.get('verified') is True and alias.get('logical_version') == metadata.get('production_candidate'),
                'Need verified production alias for the current measured batch.')
        for key in ('runtime_version','model_revision'):
            require(not str(metadata['settings'][key]).startswith('SET_'), 'Replace metadata placeholder: ' + key)
        justification = (ROOT / 'reports/promotion_justification.txt').read_text()
        require(len(justification.split()) >= 150, 'Promotion justification must contain at least 150 words.')
        markdown = (ROOT / 'reports/assignment_report.md').read_text()
        report_body = markdown.split('## ', 1)[1]
        require(500 <= word_count([('', report_body)]) <= 700, 'Report body must be 500-700 words.')
    except (ValueError, KeyError, OSError, TypeError):
        pending.append('Measured metadata, promotion or report text is pending/invalid.')
    if (ROOT / 'mlflow.db').is_file():
        try:
            from eduassist import tracking
            mlflow = tracking.initialize()
            client = mlflow.MlflowClient()
            metadata = json.loads((ROOT / 'reports/run_metadata.json').read_text())
            for summary in summaries:
                version = summary['prompt_version']
                run = client.get_run(metadata['run_ids'][version])
                require(run.data.tags.get('batch_id') == metadata['batch_id'], 'MLflow batch mismatch: ' + version)
                for metric in tracking.METRICS:
                    require(math.isclose(run.data.metrics[metric], float(summary[metric]), abs_tol=1e-10),
                            'MLflow metric mismatch: ' + version + '/' + metric)
            alias = mlflow.genai.load_prompt('prompts:/eduassist_academic_assistant@production')
            evidence = json.loads((ROOT / 'reports/production_alias.json').read_text())
            require(int(alias.version) == evidence['registry_version'], 'Live production alias disagrees with evidence.')
        except Exception:
            pending.append('Cannot verify live local MLflow runs/alias; install libraries and inspect evidence.')
    try:
        reviews = load_rows(ROOT / 'reports/human_review.csv')
        require(len(reviews) == 15 and all(r['accurate'] and r['clear'] and r['complete'] for r in reviews),
                'Inspect all 15 answers and complete reports/human_review.csv.')
    except (OSError, KeyError):
        pending.append('Human review table is missing or incomplete.')
    for name in SCREENSHOTS:
        path = ROOT / 'screenshots' / name
        require(path.is_file() and path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'),
                'Capture actual MLflow screenshot: ' + name)
    status = {'ready_for_submission': not pending, 'pending_items': pending,
              'note': 'File checks cannot establish screenshot authenticity or answer correctness; review manually.'}
    save_json(ROOT / 'submission_status.json', status)
    return status


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-pending', action='store_true', help='Report pending work without a failing exit code')
    args = parser.parse_args()
    result = verify()
    print('READY' if result['ready_for_submission'] else 'NOT READY: empirical evidence is pending or incomplete.')
    for item in result['pending_items']:
        print('- ' + item)
    raise SystemExit(0 if result['ready_for_submission'] or args.allow_pending else 1)
