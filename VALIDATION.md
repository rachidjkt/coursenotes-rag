# Validation record

## Portfolio preparation: 2026-11-16

Executed against the prepared source using the existing Windows Python 3.12 CourseNotes environment:

- `python -m unittest -v test_safety`: **6 passed**. Four deterministic citation/abstention cases use stubbed answers; two verify missing-index and invalid-k failures before model initialization. These are not model-inference results.
- `python smoke_test.py --prepare-only`: real PDF extraction, embedding/index creation, identical-index reuse, and blank-page warning assertions passed. Used the existing E5 cache through COURSENOTES_CACHE_DIR; no course PDF was used.
- `python evaluate.py smoke_data/questions.jsonl --root smoke_data --k 2 --retrieval-only --output results/retrieval-smoke`: 3 synthetic questions, 2 answerable; hit rate **2/2**, mean page Recall@2 **1.0**. Both pages fit in top 2; this checks integration, not retrieval discrimination. No abstention, answer, or timing score was produced in retrieval-only mode.
- Streamlit AppTest: initial render, question input, Ask interaction, and missing-index error display passed. No model response was mocked or presented as a real completion.
- `python core.py check`: LM Studio was reachable, but no loaded model matched default Qwen 3.5 9B. Real generation was **not executed successfully during this preparation**. The CLI reports the missing-model requirement.
- `python -m pip check`: no broken requirements in the existing environment; this does not verify a fresh installation.

A first guard-test attempt encountered sandbox temporary-directory permissions; the unrestricted local rerun passed. Fresh environment installation was not performed. No new real-course or human answer-support evaluation was run.

## Historical synthetic evidence

The existing September 30 validation note reports real local Qwen 3.5 9B generation and a synthetic Streamlit Ask interaction. Its saved aggregate CSV was inspected during preparation and supports: 3 questions, k=2, retrieval hit rate 1.0, mean Recall@2 1.0, unanswerable abstention 1/1, answerable abstention 0/2, mean response time 1.944107066684713 seconds. A sanitized transcription is in `evidence/historical_synthetic_summary.json`.

Those are historical synthetic results from the original environment, not a newly reproduced inference run or a course benchmark. Page-citation correctness does not establish semantic answer correctness. Human answer correctness and real-course quality remain unmeasured. Private raw questions/passages/results are excluded from publication.
