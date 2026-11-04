# Verification performed on this starter

Checked on 2026-11-03 using existing bundled Python 3.12.14. No additional software or model was installed to perform these checks.

- All 12 offline unit tests pass. Coverage includes distinct input/output cost formulas, hosting-cost reconciliation, strict JSON versus schema compliance, local-only endpoint validation, missing/inconsistent tokenizer usage, truncated responses, the five-success promotion gate, failure denominators, configurable report generation and all 15 scheduled prompt/question pairs.
- The workflow test uses explicit temporary fixtures and mocks the model/MLflow boundaries. It writes only to a temporary directory; its data is not in the submission CSVs. It does not establish live API or MLflow compatibility.
- Every Python module and notebook code cell parses successfully. The notebook remains deliberately unexecuted. A Jupyter kernel run has not been performed.
- Both CSV deliverables contain headers only, with no invented measurements. The submission verifier correctly reports that empirical evidence is pending.
- The draft report body contains 596 words; the planned promotion paragraph contains 217 words. Both rendered PDF pages were visually inspected for clipping and layout.
- The starter ZIP is checked for archive integrity and excludes virtualenvs, model weights, executable binaries, downloaded caches and secrets files.

Not yet verified: dependency installation, live local-server API behavior, actual answer quality, MLflow 3.5.1 registry and alias integration, measured notebook execution, final report facts, screenshot content and final submission readiness. Complete these after you supply the model and choose to install the listed dependencies.
