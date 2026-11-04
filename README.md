# EduAssist: configurable local LLMOps assignment

**Start here. This is a runnable starter, not a completed empirical submission.** The model will be supplied by you later. The CSVs currently contain headers only, the notebook is unexecuted, and the PDF is clearly labeled DRAFT. No MLflow measurements, screenshots or promotion have been invented. No Oracle or paid cloud API is used.

## What is included

| Item | Purpose | Current state |
|---|---|---|
| `eduassist_assignment.ipynb` | Readable notebook for all three tasks | Executable source; unexecuted |
| `eduassist_assignment.html` | Source-only HTML export of the notebook | Replace with executed export later |
| `eduassist/` | Small modules: configuration, API, checks, economics, experiment, MLflow, reports | Implemented; offline tests supplied |
| `settings.json` | Model/server identity, generation and cost assumptions | Edit for your local setup |
| `prompts/` | Exact basic, structured and JSON prompt wording | Ready |
| `data/academic_questions.json` | Same five academic questions and reference concepts | Ready |
| `latency_tokens_cost.csv` | All 15 measured requests, tokenizer counts and costs | Headers only |
| `prompt_evaluation_results.csv` | Three prompt summaries and recommendation | Headers only |
| `reports/assignment_report_DRAFT.pdf` | 596-word draft with a 217-word planned promotion rationale | Explicitly pending execution |
| `reports/prompt_comparison.diff` | Real differences between the supplied prompt texts | Ready |
| `screenshots/CAPTURE_GUIDE.md` | Five genuine MLflow screenshots to collect later | Pending |
| `SUBMISSION_CHECKLIST.md` | Rubric mapping and completion steps | Read before submitting |

## 1. Runtime and libraries

Python **3.12** is recommended; the standard-library code was checked with Python 3.12.14. Libraries are listed in `requirements.txt`: MLflow 3.5.1, pandas, matplotlib, nbformat, nbconvert, ipykernel and ReportLab. The model server is separate software supplied by you.

The project contains **no automatic installers, model pulls or download scripts**. The following commands install dependencies only when **you choose to run them**. Do not run them until you approve that installation yourself.

```bash
cd /absolute/path/to/mlops
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Use an existing Jupyter editor or VS Code's Jupyter support to open the notebook. The installed `nbconvert` can execute and export it without an interactive notebook server. Offline tests need only Python:

```bash
python -m unittest discover -s tests -v
python scripts/check_setup.py
```

`check_setup.py` only inspects configuration and installed libraries. It makes no API calls and downloads nothing. MLflow integration and live inference cannot be verified until you install the dependencies and supply the server.

## 2. Choose and configure an existing local server

Supply/download a model yourself later. One suitable option is [Qwen2.5-1.5B-Instruct GGUF](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF), Q4_K_M quantization. Record the actual model identity, revision/file checksum and server version you use; the project does not assume the model is present.

Edit `settings.json` with a text editor. Do not put secrets in it.

| Setting | How to use it |
|---|---|
| `endpoint_url` | Local OpenAI-compatible chat endpoint; default `http://127.0.0.1:8081/v1/chat/completions` |
| `model` | Name or alias accepted by that server; default `eduassist-local` |
| `model_source`, `model_revision` | Actual model source and revision or file SHA256; replace the `SET_...` value |
| `runtime_version`, `api_version` | Actual server version and API interface; replace the `SET_...` value |
| `max_output_tokens`, `seed` | Common generation settings for all prompts; default 512 and 42 |
| `temperature` | Kept at 0 for the controlled comparison |
| `timeout_seconds` | Timeout per request; default 180 |
| `local_api_key_env` | Optional environment variable name for authentication to a local server |
| `hosting` | Hypothetical hourly price, source, date and currency; edit together if using a different assumption |

Three examples, all using software/models you already have:

| Existing server | `endpoint_url` | `model` example |
|---|---|---|
| llama.cpp launcher below | `http://127.0.0.1:8081/v1/chat/completions` | `eduassist-local` |
| Ollama already serving a model | `http://127.0.0.1:11434/v1/chat/completions` | Your existing model name, e.g. `qwen2.5:1.5b` |
| LM Studio already serving a model | `http://127.0.0.1:1234/v1/chat/completions` | Actual loaded model identifier |

The server must return `usage.prompt_tokens`, `usage.completion_tokens` and `usage.total_tokens` from its model tokenizer. Missing or inconsistent usage is an error, not a zero-cost success. Generation must complete with `finish_reason="stop"`. API compatibility differs by server version; use your actual version in metadata.

### Optional launcher for an existing llama.cpp binary

This uses a model file and binary you supply. It does not fetch either file. GPU layers are set to zero for a predictable CPU baseline; direct server management is also supported.

```bash
export LLAMA_SERVER_PATH="/absolute/path/to/llama-server"
export LOCAL_MODEL_PATH="/absolute/path/to/model.gguf"
python scripts/start_local_model.py
```

Keep this terminal open. Record `llama-server --version` and the model SHA256 (`shasum -a 256 /path/to/model.gguf`) in `settings.json`. The configured model name is used as the server alias. If your binary uses different flags, start it manually with the equivalent localhost settings.

### Environment variables and secrets

`LOCAL_LLM_URL` optionally overrides the endpoint in settings. `LOCAL_LLM_API_KEY` is optional and is read only if the existing local server requires authentication. The supplied llama.cpp launcher requires no key. Set secret values using your preferred secret manager or private terminal session; never write them into notebooks, reports, CSVs, screenshots or ZIPs. Do not use Oracle, OpenAI or other paid API credentials.

Only literal loopback IP addresses (`127.0.0.1` or `::1`) are allowed. HTTP proxies and redirects are disabled. Enterprise `MLFLOW_TRACKING_URI` and registry settings are overridden with this project's local SQLite store.

## 3. Run and reproduce

From a second terminal in the `mlops` directory, with the selected Python environment active:

```bash
python scripts/check_setup.py
python run_assignment.py
```

Or open the notebook and set `RUN_NEW_EXPERIMENT = True` in its execution cell. Choose either method for a new run. Exporting later with the switch reset to `False` reuses genuine saved results and avoids making another 15 requests.

The workflow creates:

- `latency_tokens_cost.csv`: all 15 attempts, UTC timestamps, monotonic elapsed seconds, status, model identity, input/output/total tokens, costs and output checks.
- `reports/task1_latency_table.csv`: the five basic-prompt requests required by Task 1.
- `reports/latency_summary.csv`: mean, median, minimum, maximum and sample standard deviation for each prompt.
- `prompt_evaluation_results.csv`: the three prompt summaries and 10,000-request monthly projections.
- `evidence/<batch>/`: raw replies, exact rendered prompts and archived derived files.
- `mlflow.db`, `mlartifacts/`: real local experiment and Prompt Registry data.
- `reports/run_metadata.json`, `prompt_registry.json`, `production_alias.json`: provenance and verified promotion evidence.
- `reports/prompt_metrics.png`, `assignment_report.pdf`, `assignment_report.md`, `promotion_justification.txt`: charts and source-grounded report.

The experiment name is exactly `eduassist_llmops_assignment`. All five required metrics are logged for each prompt. The original prompt wording is preserved and only prompt wording changes. Request order rotates across questions; no retries, warmups, JSON grammar or forced schema mode are used. First-call initialization can affect latency. Prompt caching is disabled in the request where supported; verify your server honors it. Temperature zero and a fixed seed do not guarantee identical output across machines or server versions.

If requests fail, inspect the response status and raw evidence. Fix the local setup and rerun. Failed and truncated responses remain visible, are counted as JSON failures and block promotion. The workflow does not silently substitute fabricated answers. A prior alias in an existing database is not evidence of a successful new batch: consult `production_alias.json` and `batch_id`.

## 4. Understand the cost estimate

The default **hypothetical hosting assumption** is [HF AWS intel-spr x4, 4 vCPU, 8 GB RAM at USD 0.134/hour](https://huggingface.co/docs/inference-endpoints/pricing), checked **2026-11-03**. No cloud resource is created.

If every measured reply provides llama.cpp prompt/generation timings:

```text
input USD/million = hourly USD x sum(input processing seconds) / 3600
                    / sum(input tokens) x 1,000,000
output USD/million = hourly USD x sum(generation seconds) / 3600
                     / sum(output tokens) x 1,000,000
```

Otherwise a transparent fallback pools measured HTTP latency over total tokens and uses the same effective rate for input and output. One common set of pooled rates applies to all prompts. The actual method and rates are saved in run metadata.

```text
input cost = input tokens / 1,000,000 x input rate
output cost = output tokens / 1,000,000 x output rate
total request cost = input cost + output cost
projected monthly cost = mean request cost x 10,000
```

This is the assignment's allowed local-model alternative. **These are effective hosting estimates, not advertised per-token API tariffs.** Mac throughput is not the reference cloud throughput. Idle capacity, warmup, electricity and provider minimum billing are excluded. Actual external inference spend is zero. Shorter responses can reduce output processing; reassess quality before changing the cap.

## 5. Review quality and promotion

Strict JSON parsing and exact schema checks are separate. All five attempts form the JSON denominator. `quality_score` is reference-concept coverage, not a validated factual judge. Read the actual answers and fill `reports/human_review.csv` with your own observations.

A candidate needs five successes, JSON validity 100%, schema compliance 100%, and concept coverage >=80%. Eligible versions are ranked by concept coverage, estimated cost, then latency. The selected registry version is assigned alias `production` and loaded back for verification. No version is presumed best before testing. If no version qualifies, no new promotion is made: improve the local model/setup and rerun before submitting. Confidence labels are not calibrated probabilities.

## 6. MLflow UI, screenshots and notebook export

```bash
python scripts/start_mlflow.py
```

Open `http://127.0.0.1:5000`. The equivalent MLflow UI command, from this directory, is:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000
```

Follow `screenshots/CAPTURE_GUIDE.md` to save the five genuine screenshots. No screenshots are included yet because no run has occurred.

Reset `RUN_NEW_EXPERIMENT = False`, then execute all notebook cells and export:

```bash
jupyter nbconvert --to notebook --execute --inplace eduassist_assignment.ipynb --ExecutePreprocessor.timeout=3600
jupyter nbconvert --to html eduassist_assignment.ipynb
```

The measured report is a separate required PDF; HTML satisfies the notebook-export requirement. Read and personalize the 500-700 word report, preserving measured facts and a justification of at least 150 words. Remove draft material from your final submission using the packager below.

## 7. Verify and package

```bash
python -m unittest discover -s tests -v
python scripts/verify_submission.py
python scripts/package_submission.py
```

The verifier returns nonzero while empirical evidence is pending. The packager refuses a final submission when checks fail. To share the starter deliberately, use `python scripts/package_submission.py --allow-incomplete`; its ZIP is named `mlops_starter.zip` and retains the draft labels. Final packaging excludes secrets, models, binaries, virtualenvs and draft PDFs.

When moving to another directory, absolute artifact locations inside MLflow SQLite may refer to the original machine. The CSVs and raw replies remain portable. With dependencies installed, `python scripts/restore_tracking.py` can rebuild local MLflow views from the saved measured summaries without calling a model. Never restore from the currently empty starter CSVs.

## Assessment and source notes

See `SUBMISSION_CHECKLIST.md` for the full 2+3+5 mark mapping. Full marks cannot be guaranteed; the evaluator decides whether the evidence satisfies the brief. The local-model exception and hosting assumptions are stated explicitly. This starter used AI assistance: review your course rules, disclose assistance as required, and submit only work you have executed, inspected and can explain.
