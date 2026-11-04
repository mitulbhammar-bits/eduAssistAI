"""Real MLflow Prompt Registry operations, imported only when an experiment runs."""
import hashlib
import json
from pathlib import Path
from .config import ROOT, EXPERIMENT, PROMPT_NAME, tracking_uri

METRICS = ['avg_latency_seconds', 'avg_input_tokens', 'avg_output_tokens',
           'avg_cost_per_request', 'valid_json', 'schema_valid_rate', 'quality_score',
           'projected_monthly_cost_usd', 'request_count', 'success_count']
COMMIT_MESSAGES = {
    'v1': 'Basic academic answer baseline from the assignment.',
    'v2': 'Add academic role, concise accurate answers and undergraduate language.',
    'v3': 'Require JSON only with answer, confidence and key_points fields.'}


def initialize():
    # Avoid inherited enterprise destinations and telemetry from the local experiment.
    import os
    os.environ['MLFLOW_ENABLE_TELEMETRY'] = 'false'
    import mlflow
    mlflow.set_tracking_uri(tracking_uri())
    mlflow.set_registry_uri(tracking_uri())
    experiment = mlflow.get_experiment_by_name(EXPERIMENT)
    if experiment is None:
        mlflow.create_experiment(EXPERIMENT, artifact_location=(ROOT / 'mlartifacts').as_uri())
    mlflow.set_experiment(EXPERIMENT)
    return mlflow


def register_prompts(templates):
    mlflow = initialize()
    path = ROOT / 'reports' / 'prompt_registry.json'
    old = json.loads(path.read_text()) if path.exists() else {}
    registry = {}
    for logical, template in templates.items():
        fingerprint = hashlib.sha256(template.encode()).hexdigest()
        previous = old.get(logical)
        prompt = None
        if previous and previous.get('sha256') == fingerprint:
            try:
                prompt = mlflow.genai.load_prompt(previous['uri'])
            except Exception:
                prompt = None  # Database may have been moved or deliberately rebuilt.
            if prompt is not None and prompt.template != template:
                prompt = None
        if prompt is None:
            prompt = mlflow.genai.register_prompt(name=PROMPT_NAME, template=template,
                commit_message=COMMIT_MESSAGES[logical], tags={'logical_version': logical})
        registry[logical] = {'name': PROMPT_NAME, 'version': int(prompt.version),
            'uri': f'prompts:/{PROMPT_NAME}/{prompt.version}', 'sha256': fingerprint,
            'commit_message': COMMIT_MESSAGES[logical], 'template': template}
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(registry, indent=2) + '\n')
    return registry


def log_results(summaries, registry, settings, batch_id, measured_files):
    mlflow = initialize()
    run_ids = {}
    for summary in summaries:
        version = summary['prompt_version']
        with mlflow.start_run(run_name=f'{version}_{batch_id}') as run:
            mlflow.log_params({'model': settings['model'], 'prompt_version': version,
                'prompt_uri': registry[version]['uri'], 'temperature': settings['temperature'],
                'max_output_tokens': settings['max_output_tokens'], 'seed': settings['seed'],
                'pricing_date': settings['hosting']['pricing_date'], 'currency': 'USD',
                'api_version': settings['api_version'], 'model_revision': settings['model_revision'],
                'runtime_version': settings['runtime_version'], 'cost_basis': 'local hosting estimate'})
            mlflow.set_tags({'batch_id': batch_id, 'evidence_type': 'local_model_measurements',
                             'external_inference_spend_usd': '0'})
            mlflow.log_metrics({metric: float(summary[metric]) for metric in METRICS})
            for path in measured_files:
                mlflow.log_artifact(str(path), artifact_path='evidence')
            mlflow.log_text(registry[version]['template'], 'prompt.txt')
            run_ids[version] = run.info.run_id
    return run_ids


def promote(version, registry):
    mlflow = initialize()
    entry = registry[version]
    mlflow.genai.set_prompt_alias(PROMPT_NAME, 'production', entry['version'])
    loaded = mlflow.genai.load_prompt(f'prompts:/{PROMPT_NAME}@production')
    if loaded.template != entry['template'] or int(loaded.version) != entry['version']:
        raise RuntimeError('Production alias readback did not match the selected prompt.')
    return {'alias': 'production', 'prompt_name': PROMPT_NAME,
            'logical_version': version, 'registry_version': entry['version'],
            'uri': f'prompts:/{PROMPT_NAME}@production', 'verified': True}
