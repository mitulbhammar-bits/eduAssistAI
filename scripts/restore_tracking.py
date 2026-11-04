"""Rebuild local MLflow views from genuine saved CSVs after extracting elsewhere.

Uses saved measurements only. It does not call the model or invent results.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eduassist.config import ROOT
from eduassist.files import load_rows, save_json
from eduassist.experiment import read_inputs
from eduassist.evaluation import choose_prompt
from eduassist import tracking

rows = load_rows(ROOT / 'prompt_evaluation_results.csv')
if len(rows) != 3:
    raise SystemExit('No completed saved evaluation is available to restore.')
summaries = [{k: (v if k in {'prompt_version', 'recommended'} else float(v))
              for k, v in row.items()} for row in rows]
metadata_path = ROOT / 'reports' / 'run_metadata.json'
metadata = json.loads(metadata_path.read_text())
templates, _ = read_inputs()
registry = tracking.register_prompts(templates)
run_ids = tracking.log_results(summaries, registry, metadata['settings'],
    metadata['batch_id'] + '_restored', [ROOT / 'latency_tokens_cost.csv',
        ROOT / 'prompt_evaluation_results.csv', metadata_path])
selected = choose_prompt(summaries)
if selected:
    save_json(ROOT / 'reports' / 'production_alias.json', tracking.promote(selected, registry))
metadata['restored_run_ids'] = run_ids
save_json(metadata_path, metadata)
print('Restored saved evidence without inference:', run_ids)
