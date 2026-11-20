# Validation record: 2026-11-16

This section records the current implementation. Earlier baseline notes are preserved below as historical evidence and do not describe the current loaded-model status.

## Executed checks

- **26 regression tests passed**, using `python -m unittest -v test_safety test_evaluation`: compatible/incompatible/missing/corrupt/legacy manifests, embedding and chunk configuration mismatches, both assistant and retrieval-only load paths, cited/uncited mixed claims, extra prose, invented pages/files, separate multiple claims, French text, abstention, physical PDF labels, split integrity, and page-deduplicated metrics.
- `python -m pip check`: no broken requirements in the existing Python 3.12 environment. No dependency was added or model downloaded. A fresh installation was not executed.
- `python demo.py --prepare-only`: original synthetic PDF indexed successfully into **33 chunks**, with no extraction warnings. Repeated preparation reused the compatible index.
- `python core.py check`: a real completion returned CONNECTED from the existing local Qwen model after loading its already-present weights.
- Development and held-out retrieval-only runs and real Qwen generation runs all completed with **zero execution errors**. Retrieval-only summaries and generation summaries are saved separately.
- Streamlit AppTest: initial render and the real Qwen Ask interaction with synthetic input passed. The real browser also verified English/French accepted cited output, source inspection, and unsupported-question abstention. Three unedited screenshots and a text receipt are included; no video was fabricated. Browser capture required explicit forwarding of the same local LM Studio endpoint; the demo launcher now resolves it before starting Streamlit. See docs/DEMO.md.

## Preliminary synthetic measurements

All retrieval metrics use the **initial top 3 of 33 chunks**, deduplicated by physical page. There are 18 corpus pages. Development has 9 answerable/3 unsupported questions; held out has 12 answerable/4 unsupported questions. Nine questions across the splits explicitly request cross-language retrieval; the held-out set also includes three multi-page comparisons.

| Split | Questions | Hit rate@3 | Mean page Recall@3 | All support@3 | Answerable abstentions | Unsupported abstentions | Citation failures | Mean latency | Median | P95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Development | 12 | 100.0% | 100.00% | 100.00% | 0/9 | 3/3 | 0 | 4.883 s | 4.326 s | 8.675 s |
| Held out | 16 | 100.0% | 95.83% | 91.67% | 0/12 | 4/4 | 0 | 5.915 s | 6.204 s | 12.206 s |

Citation failures mean output-format, sentence-coverage or retrieved-page-reference rejection, not a factual-support judgment. Model/evidence abstentions are distinguished from validation failures. A non-abstaining answer is not automatically complete or correct. Unsupported-abstention fractions concern these few authored questions, not a general accuracy estimate.

Latency is sequential per-question wall time including retrieval, relevance, optional rewrite and generation, excluding indexing, initialization and model loading. P95 uses the nearest-rank sample percentile. Separate retrieval-only mean latency was 0.0226 s (development) and 0.0218 s (held out); these are machine-specific observations with cached embeddings. They are not comparable to a fresh startup or another machine.

## Evaluated model, settings, corpus and revision

- Language model: **qwen/qwen3.5-9b**, GGUF **Q4_K_M**, loaded as **coursenotes-qwen** in LM Studio from existing local weights.
- Context: **8192 tokens**. Load configuration (including four configured parallel slots) is recorded in each generation provenance file; benchmark requests were sequential.
- Requests: temperature **0**, maximum output **700 tokens**, no streaming, reasoning_effort **none**, enable_thinking **false**. No request seed was set; temperature zero does not guarantee identical results.
- Embeddings: **intfloat/multilingual-e5-small**, CPU, normalized, passage/query prefixes; 900-character chunks and 150-character overlap.
- Corpus: **meridian-synthetic-v1**. PDF SHA-256: `4950c211e975de12354636c44f70d923b3a54c753805bac08144975aad096e53`.
- Evaluated source commit: **`4fdbdb8cd845959a02a3035e5841ef1e1c86fa5b`**. All four provenance records report `evaluated_source_dirty=false`; core/evaluator working-file hashes are included. Source, configuration and fixtures were committed before evaluation.
- The synthetic corpus/questions/reference answers were authored for this project by the coding assistant. Labels are author-defined; quote/extraction checks are not independent human review. All human factual-correctness/source-support review fields remain blank.

`evaluation/synthetic_v1/protocol.json` records the fixed protocol and file hashes. `evaluation/runs/*-v1/provenance.json` records exact dataset hash, index configuration and corpus hash, model load configuration, request settings, package versions, source hashes and start time. Each run has inspectable `answers.jsonl`, summaries and an editable `review.csv`. No private course material, credentials, weights or generated vector index is published.

## Hold-out discipline and visible failure case

The 12 development and 16 held-out questions were separated before execution. The held-out split was run once in retrieval-only mode and once in generation mode using the same frozen code and k=3; no prompt, retrieval setting, reference label or pipeline source was tuned on those results. After evaluation, only documentation and demo/browser-capture behavior changed: the demo now explicitly uses the already-fixed k=3, forwards the verified local endpoint to Streamlit, and disables file watching. Core retrieval/generation and evaluator source hashes remain identical to the frozen run; no held-out evaluation was rerun. Screenshots use separate live development-question interactions. The set is now published and cannot serve as an unseen test for future tuning.

The retained **held10** example asks for Atlas and Boreal return windows/remedies. Initial retrieval returned pages **1, 3, 1** and missed expected page **2**. The automatic relevance check accepted the passages without rewriting; the answer has valid Atlas page references but omits Boreal's specific window/remedy. It is not labeled correct. This illustrates why 100% hit rate, no answerable abstentions, and zero citation-validation failures do not establish complete answers.

No human correctness rate or semantic source-support score is reported. The dataset is small, synthetic, author-labeled, and includes explicit absent-information cues; these preliminary outcomes do not establish real-course quality. The sentence-boundary guard is conservative and heuristic. Valid references do not prove factual support or eliminate hallucinations. Older two-page smoke results are a different, easier fixture and cannot substantiate a measured improvement.

---

## Historical baseline record (before this update)

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


## Reproduction and configuration reference

The following commands document deliberate reproduction, not checks rerun for the November 20 documentation polish. They require the local Qwen model and embedding setup described in the README. Use new output directories to preserve the saved results.

```powershell
.\.venv\Scripts\python.exe demo.py --prepare-only
$env:COURSENOTES_HOME = (Join-Path (Get-Location) '.demo_runtime')
.\.venv\Scripts\python.exe evaluate.py evaluation/synthetic_v1/development.jsonl --k 3 --retrieval-only --output evaluation/runs/my-dev-retrieval
.\.venv\Scripts\python.exe evaluate.py evaluation/synthetic_v1/development.jsonl --k 3 --output evaluation/runs/my-dev-generation
# Freeze source/configuration before held-out use; do not tune on its results.
.\.venv\Scripts\python.exe evaluate.py evaluation/synthetic_v1/held_out.jsonl --k 3 --retrieval-only --output evaluation/runs/my-held-retrieval
.\.venv\Scripts\python.exe evaluate.py evaluation/synthetic_v1/held_out.jsonl --k 3 --output evaluation/runs/my-held-generation
```

The released held-out set is visible; rerunning it is not a new independent evaluation. `COURSENOTES_HOME` relocates indexes/results and default document/cache folders. `COURSENOTES_DOCUMENTS_DIR` selects authorized PDFs, `COURSENOTES_CACHE_DIR` selects an existing embedding cache, and `COURSENOTES_EMBED_MODEL` changes embeddings and requires reindexing. Set variables before starting Python; `.env.example` is not loaded automatically. `LM_STUDIO_URL` must be loopback HTTP; otherwise CLI discovery locates the server. `COURSENOTES_MODEL` selects a loaded model or identifier, and `LM_STUDIO_API_TOKEN` is local-only if authentication is enabled. The demo fixes its own documents/runtime and k=3; the normal app defaults to k=4 via `COURSENOTES_TOP_K`.

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_safety test_evaluation
.\.venv\Scripts\python.exe core.py check
```

The connectivity command requires the loaded local model. Missing, legacy, or incompatible manifests require reindexing with `python core.py index` under the correct runtime/document settings. Loading validates configuration but does not rehash the current document folder; content hashes are checked during indexing. Temperature zero does not guarantee identical inference across hardware or runs.


## Documentation review: 2026-11-20

Reviewed the published source, dependency declarations, Git history, and saved evidence against the README. Checked Markdown fences, relative links, screenshot paths where applicable, and whitespace. The update changes documentation only; runtime source, notebooks, configurations, scores, and evidence files are preserved. No dependency installation, model/data download, training, or held-out evaluation was performed. Historical execution results above were not rerun.
