# Rubric and submission checklist

**Current state: runnable starter. All measured results, MLflow execution, final report and screenshots are pending.** No model or software will be downloaded automatically. The checks below describe what you must verify after supplying your model.

| Marks | Requirement | Code/artifact | Completion evidence |
|---|---|---|---|
| Task 1: 2 | API call for five academic questions | `eduassist/api.py`, `data/academic_questions.json`, notebook sections 3-5 | Five successful basic-prompt requests |
| | API key from environment | `LOCAL_LLM_API_KEY`, `eduassist/api.py` | Optional for authenticated local endpoints; no key needed for unauthenticated local alternative |
| | ID, version, model, start/end time, latency, status | `latency_tokens_cost.csv`, `reports/task1_latency_table.csv` | Filled tables from actual calls |
| | Mean, median, min, max, standard deviation | `reports/latency_summary.csv` | Five successful observations per version; sample std documented |
| | Slowest request interpretation | Notebook and generated report | Observed ID/time and cautious possible explanations |
| Task 2: 3 | Actual tokenizer counts | API `usage` fields preserved in `evidence/<batch>/` | Input + output = total for every call |
| | Input/output/request cost formulas | `eduassist/economics.py`, notebook section 6 | CSV arithmetic matches effective rates |
| | Monthly projection for 10,000 requests | `prompt_evaluation_results.csv` | Mean request cost x 10,000 |
| | Published rates and cost optimization | Settings, README, run metadata, report | USD, pricing date/source and local hosting-estimate disclosure |
| Task 3: 5 | Exact experiment name | `eduassist/tracking.py` | `eduassist_llmops_assignment` in MLflow |
| | Register exact v1, v2, v3 with commit messages | `prompts/`, registry snapshot | Real Prompt Registry versions |
| | Same five questions for all prompts | `eduassist/experiment.py` | 15 rows; one row for each version/question pair |
| | Five required logged metrics | `eduassist/tracking.py` | Three MLflow runs with all required metrics |
| | v3 valid_json = valid / total | `eduassist/evaluation.py` | Correct five-attempt denominator; syntax distinct from schema |
| | Comparison table and prompt diff | `prompt_evaluation_results.csv`, diff, notebook | Three complete summary rows and readable comparison |
| | Promote best version using production alias | `tracking.promote`, alias snapshot | Alias readback agrees with latest recommendation |
| | Justification >=150 words | Generated `reports/promotion_justification.txt` | Covers quality, JSON, latency, tokens and cost |
| Submission | Executed Jupyter notebook + exported HTML | `eduassist_assignment.ipynb`, `.html` | All code cells executed; no errors; export contains measured results |
| | requirements.txt | Root file | Install tested in your environment |
| | Five MLflow screenshots | `screenshots/` | All five real, readable views from current batch |
| | Final PDF report, 500-700 words | Generated `reports/assignment_report.pdf` | Replace draft; facts match CSVs; personalize after review |
| | README reproduction details | `README.md` | Python/libraries/env/install/UI/reproduction all documented |
| | One ZIP | `scripts/package_submission.py` | Verifier passes; final ZIP excludes secrets and model weights |

Before submitting:

- [ ] Supply your own local model and server, and install libraries only when you choose.
- [ ] Replace model revision/server-version placeholders in settings; verify hosting assumptions.
- [ ] Run the experiment; confirm all 15 attempts succeed and the five-per-version comparison is fair.
- [ ] Inspect every answer for factual accuracy and complete `reports/human_review.csv`.
- [ ] Confirm the JSON candidate qualifies and the latest production alias readback is verified.
- [ ] Execute the notebook, export HTML, review the measured PDF and capture all screenshots.
- [ ] Run the verifier and create the final ZIP.
- [ ] Check course rules, add your permitted identity details if required, and disclose assistance as required.

This checklist maps the supplied brief; it is not a prediction or guarantee of marks.
