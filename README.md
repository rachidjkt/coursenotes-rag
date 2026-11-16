# CourseNotes: local bilingual document assistant

CourseNotes answers English and French PDF questions using local retrieval and LM Studio. I built this project to explore document ingestion, inspectable answers, bounded LangGraph orchestration, and evaluation that separates retrieval from answer generation.

**Status:** implemented Streamlit application with a real local Qwen evaluation on an original **synthetic, preliminary** retail-operations corpus. No real-course benchmark, human answer-correctness score, or production-readiness claim is made. See [VALIDATION.md](VALIDATION.md) for actual results and [the demonstration outline](docs/DEMO.md) for an 85-second recording.

## Run the shareable demonstration

From the repository root, with Python 3.12 and LM Studio:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
lms server start
lms load qwen/qwen3.5-9b --identifier coursenotes-qwen --context-length 8192
.\.venv\Scripts\python.exe demo.py
```

Open `http://127.0.0.1:8501`. `demo.py` uses only the supplied synthetic PDF, fixes retrieval at k=3, and stores its generated index in ignored `.demo_runtime/`. It resolves the local model-server endpoint before starting Streamlit and disables file watching for this recording workflow. No language-model weights are distributed or downloaded by the launcher. Qwen must already exist in LM Studio; do not substitute another model when reproducing this evaluation. E5 embeddings may download on first indexing unless cached.

Use **Save and index PDFs** for authorized personal documents in the normal app (`python -m streamlit run app.py`). Keep personal documents separate from the shareable demonstration. Scanned PDFs need OCR, which is not implemented.

## Architecture and implemented safeguards

1. PyPDFLoader extracts physical pages; RecursiveCharacterTextSplitter uses 900-character chunks with 150-character overlap.
2. CPU `intfloat/multilingual-e5-small` uses `passage:`/`query:` prefixes and normalized embeddings. LangChain InMemoryVectorStore retrieves by cosine similarity and persists JSON vectors.
3. LangGraph performs retrieval, automatic local-model relevance judgment, at most one rewrite/retrieval retry, and answer generation or abstention. There is no unbounded agent loop.
4. Before assistant or retrieval-only loading, a shared validator checks manifest schema, embedding model, chunking, extraction/splitter version, normalization and prefixes. Missing, corrupt, legacy or incompatible manifests require reindexing before embeddings/model initialization. Content hashes trigger rebuilding during indexing; loading does not rehash the current document folder.
5. The model returns JSON claims: each claim contains one sentence and a nonempty list of filename/page references. Uncited prose, extra output fields, multi-sentence claim text, empty references, and references outside retrieved passages cause the entire answer to be withheld. Accepted claims are rendered with individual citations.

Citation coverage and valid retrieved page references **do not prove factual support**. Sentence-boundary validation is deliberately conservative and heuristic; complex abbreviations or multi-clause claims can need review. A model can still attach a valid page to an unsupported claim. These checks do not eliminate hallucinations. Invalid output is counted separately from a model/evidence abstention.

## Synthetic evaluation

[Meridian v1](evaluation/synthetic_v1/corpus.json) is an original fictional operations handbook: 18 physical pages, 33 indexed chunks, and **top-k=3**. Similar return policies, retention periods, inventory states, shipping targets, and metric definitions act as distractors. No actual merchant, customer, course, or payment data is included.

The 28 questions are split before execution:

- **Development:** 12 questions (9 answerable, 3 unsupported), including English, French and cross-language retrieval.
- **Held out:** 16 questions (12 answerable, 4 unsupported), including cross-language and multiple-page comparisons.

Questions include authored reference answers and physical supporting pages. Single-page supporting quotes are checked against PDF extraction. Labels are synthetic author definitions, not independent human review. Code, data hashes and settings were committed before the held-out run; its results were reported without tuning against them. [Protocol and fixture hashes](evaluation/synthetic_v1/protocol.json) document the fixed setup.

Current preliminary results (full methods and limitations in [VALIDATION.md](VALIDATION.md)):

| Split | Hit@3 | Page Recall@3 | Answerable abstention | Unsupported abstention | Citation failures | Mean response |
|---|---:|---:|---:|---:|---:|---:|
| Development | 9/9 | 100% | 0/9 | 3/3 | 0 | 4.88 s |
| Held out | 12/12 | 95.83% | 0/12 | 4/4 | 0 | 5.92 s |

All four runs had zero execution errors. The held-out comparison held10 missed one expected page and omitted the corresponding Boreal details despite valid citations. Human correctness/support remain unscored; zero citation failures is not zero factual errors.

Inspect [development generation](evaluation/runs/development-generation-v1/answers.jsonl), [held-out generation](evaluation/runs/held-out-generation-v1/answers.jsonl), and the corresponding `summary.json` and `provenance.json` files. Separate retrieval-only runs use the same initial top-k metric. Each run includes a blank `review.csv` for you to mark factual correctness, source support, language appropriateness, and reviewer notes. No generated answer has been assigned an invented human correctness judgment.

To reproduce in **new output directories** after preparing the demo:

```powershell
.\.venv\Scripts\python.exe demo.py --prepare-only
$env:COURSENOTES_HOME = (Join-Path (Get-Location) '.demo_runtime')
.\.venv\Scripts\python.exe evaluate.py evaluation/synthetic_v1/development.jsonl --k 3 --retrieval-only --output evaluation/runs/my-dev-retrieval
.\.venv\Scripts\python.exe evaluate.py evaluation/synthetic_v1/development.jsonl --k 3 --output evaluation/runs/my-dev-generation
# Freeze source/configuration before held-out use; do not tune on its results.
.\.venv\Scripts\python.exe evaluate.py evaluation/synthetic_v1/held_out.jsonl --k 3 --retrieval-only --output evaluation/runs/my-held-retrieval
.\.venv\Scripts\python.exe evaluate.py evaluation/synthetic_v1/held_out.jsonl --k 3 --output evaluation/runs/my-held-generation
```

The released held-out set is now visible; a future tuned iteration needs a new held-out set. Re-running these questions does not create a fresh independent evaluation.

## Configuration and reproducibility

`.env.example` is a template and is not automatically loaded. Set environment variables before launching:

```powershell
$env:COURSENOTES_DOCUMENTS_DIR = 'C:\path\to\authorized-pdfs'
$env:COURSENOTES_CACHE_DIR = 'C:\path\to\existing-embedding-cache'
$env:LM_STUDIO_URL = 'http://127.0.0.1:1234'
$env:COURSENOTES_MODEL = 'coursenotes-qwen'
```

`COURSENOTES_HOME` relocates indexes/results and default document/cache folders. `COURSENOTES_EMBED_MODEL` changes embeddings; reindex afterward. Loopback HTTP is required for `LM_STUDIO_URL`; otherwise the local CLI discovers the port. Set `LM_STUDIO_API_TOKEN` locally only if server authentication is enabled. Never commit it. The demo launcher chooses its own isolated runtime/documents and k=3 while honoring cache/model settings. The normal app retains default k=4, configurable through `COURSENOTES_TOP_K`.

`requirements.txt` pins existing direct dependencies; no new runtime dependency was added. `requirements-lock.txt` is a historical Windows environment snapshot, not a cross-platform lock. Current evaluation provenance records model quantization, loaded identifier/context, request settings, package versions, source commit/hashes, corpus hashes, and initialization/latency definitions. Temperature zero does not guarantee identical inference across devices/runs.

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_safety test_evaluation
.\.venv\Scripts\python.exe core.py check
```

Legacy manifests deliberately fail until reindexed using `python core.py index` with the correct runtime/document environment. On Linux use `.venv/bin/python` instead of the Windows executable.

## Main files and limitations

| File | Role |
|---|---|
| `core.py` | Ingestion, compatible index loading, embeddings, graph, local model client, claim validation |
| `app.py`, `demo.py` | Existing Streamlit workflow and isolated synthetic demo launcher |
| `evaluate.py` | Retrieval/generation metrics, sanitized outputs, provenance, human review sheet |
| `evaluation/build_synthetic.py` | Original fixture source and deterministic shareable PDF builder |
| `test_safety.py`, `test_evaluation.py` | Manifest, citation, fixture and metric regressions; stubbed answers are not inference evidence |
| `demo/capture_demo.mjs` | Optional dependency-free capture of the real running UI with an existing browser |

No OCR, production authentication, large-corpus validation, semantic entailment checker, or clinically/legally relevant dataset is supplied. Relevance judgment is automatic and can be wrong. Valid citations can accompany false claims. Synthetic preliminary results cannot establish real-course quality. A fresh dependency installation was not tested in this update; the existing environment was used.

Remaining focused improvements are human review of saved answers and, later, a separately labeled real-document evaluation—not another architecture rewrite.

## Data, attribution and rights

Private PDFs, credentials, model weights, vector indexes, caches, and private raw results remain ignored. Only the explicitly allowed original synthetic PDF, fixture, sanitized evaluation outputs and actual UI screenshots are shared in this private repository. The original source/history is preserved.

Streamlit, LangChain, LangGraph, Sentence Transformers, PyPDF, ReportLab, E5 and Qwen retain their respective licenses and terms. No pretrained-model or third-party authorship is claimed. No project-wide license grant is added while historical ownership is not independently established. Use only documents you may process; private visibility does not grant redistribution rights.
