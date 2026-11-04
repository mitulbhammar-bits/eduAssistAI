# Capture genuine MLflow evidence after running

There are deliberately no screenshots yet. Do not replace them with generated images or empty UI views. Start `python scripts/start_mlflow.py` and open `http://127.0.0.1:5000` after collecting the 15 real requests.

Save PNG screenshots under this directory with these exact names:

| File | Capture |
|---|---|
| `01_experiment.png` | Experiment `eduassist_llmops_assignment`, showing all three runs from the same batch and their v1/v2/v3 names |
| `02_prompt_registry.png` | Prompt `eduassist_academic_assistant` and the three registered versions/commit messages; use logical version tags if registry numbers exceed 3 after edits |
| `03_metrics.png` | Run comparison with `avg_latency_seconds`, `avg_input_tokens`, `avg_output_tokens`, `avg_cost_per_request` and `valid_json` visible; use more than one image if needed |
| `04_prompt_diff.png` | Registry comparison of v2 and v3, showing the JSON-only instructions and schema changes |
| `05_production_alias.png` | The chosen prompt version with alias `production`; it must agree with `reports/production_alias.json` for the latest batch |

Use the normal screenshot feature on your computer. Keep the experiment/prompt names, version and relevant values readable. Never show secrets, browser account details or personal data. The sidebar and controls may differ by MLflow version.

The source diff at `reports/prompt_comparison.diff` is supplemental comparison evidence, not a replacement for the requested MLflow screenshots. If the registry UI has no diff control, capture the actual version details and the text diff together, clearly showing which versions are compared.

After capturing, run `python scripts/verify_submission.py`. A PNG's presence alone does not prove its content: inspect each image yourself and confirm it belongs to the latest batch.
