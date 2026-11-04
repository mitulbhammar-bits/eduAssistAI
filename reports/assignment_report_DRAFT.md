# EduAssist LLMOps assignment report

Status: Draft - execution pending. Body: 596 words. Promotion justification: 217 words.

## Purpose and execution status

DRAFT: no model inference, MLflow runs or screenshots have been collected. EduAssist needs academic answers in a dependable JSON interface. MLOps primarily manages data, training, models and deployment; LLMOps also versions prompts, context, output constraints and inference economics. The assignment permits an open-source local model. No paid API or Oracle billing is used, and external inference spend is zero.

## Controlled method

The same five academic questions are evaluated with the exact basic, structured and JSON prompt templates. Only prompt wording changes. Temperature zero, seed 42 and a common 512-token output cap limit variation; deterministic output is not guaranteed. Prompt order rotates across questions. There are no retries or grammar-enforced JSON shortcuts. The local API, configured model identity and server version are preserved in run metadata. Input and output counts come from the serving model tokenizer, never character-length guesses.

## Latency interpretation

Latency results are pending because the model has not been supplied or run. The five-row Task 1 table will use basic-prompt requests; the complete CSV will contain all fifteen attempts. UTC timestamps document when requests occur, while a monotonic clock measures elapsed time. Mean, median, minimum, maximum and sample standard deviation will be calculated from successful requests. Longer generated answers, initial model preparation and CPU scheduling are possible causes of a slow request, not findings from this unexecuted draft.

## Token economics

Cost results and monthly projections are pending. Each cost will equal input tokens divided by one million times the input rate, plus output tokens divided by one million times the output rate. The mean is multiplied by 10,000 for the monthly estimate. The configurable reference is Hugging Face AWS intel-spr x4 at USD 0.134/hour, checked on 3 November 2026. Measured local throughput will convert this hosting assumption into effective token rates. These are estimates, not cloud invoices; shorter responses are the initial optimization recommendation.

## Promotion justification

No prompt has been promoted because there are no measured responses yet. The intended choice is evidence-driven: the structured JSON prompt is a candidate rather than a presumed winner. Actual comparisons of quality, JSON validity, latency, tokens and cost will be inserted after the local experiment. Promotion requires five successful requests, a JSON syntax pass rate of one, exact schema compliance of one and concept coverage of at least eighty percent. Among eligible prompts, higher concept coverage takes priority, followed by lower estimated cost and lower mean latency. This reflects EduAssist's requirement that downstream software reliably read answer, confidence and key_points. A faster prose answer cannot satisfy that interface merely by costing less. Concept matching is a transparent quality proxy, not proof of factual accuracy, and confidence labels are not calibrated probabilities. The saved responses therefore need human inspection before wider use. Schema checks reject wrong fields, invalid confidence values and empty key points; JSON parsing rejects code fences and duplicate keys. Failed and truncated responses block promotion instead of disappearing from the denominator. Longer prompts can increase input consumption, while JSON structure can increase output consumption. Those tradeoffs must be accepted using the observed token counts and hosting estimate. Five questions cannot establish production reliability; broader questions and repeated runs are necessary before deployment.

## Reproducibility and limits

The notebook, CSVs, raw replies, prompt diffs and MLflow records connect the results to their sources. Reproduction requires user-supplied model software and dependencies. API secrets, if local authentication is enabled, come from an environment variable. Capture the five requested MLflow views after execution and review the final submission checklist. Pricing source: huggingface.co/docs/inference-endpoints/pricing; registry guidance: mlflow.org/docs/latest/genai/prompt-registry/.
