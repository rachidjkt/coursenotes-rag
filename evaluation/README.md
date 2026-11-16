# Evaluation artifacts

All files in `synthetic_v1/` and `runs/*-v1/` concern the original fictional Meridian corpus. The coding assistant authored the synthetic handbook, questions, and reference answers for this project. These are author-defined labels, not real merchant policies, user course content, or independent human judgments. Supporting quotes were checked by construction and PDF extraction; comparative references remain author-defined.

- `synthetic_v1/corpus.json` and `meridian.pdf`: 18 inspectable physical pages.
- `development.jsonl`: 12 development questions; `held_out.jsonl`: 16 separately fixed held-out questions. Both include reference answers and expected pages.
- `protocol.json`: fixed k=3, 900/150 chunking, split sizes, and fixture SHA-256 hashes. The supplied PDF produces 33 chunks.
- `runs/development-retrieval-v1` and `runs/held-out-retrieval-v1`: retrieval-only results, with no local-model calls.
- `runs/development-generation-v1` and `runs/held-out-generation-v1`: real local Qwen outputs from the same frozen source and corpus.

Each run contains `answers.jsonl` (questions, reference answers, initial/final passages, raw/validated model output where generated, timings, errors), `summary.json`, `summary.csv`, `provenance.json`, and `review.csv`. No credentials, absolute personal paths, weights, or generated vector indexes are included. Historical evidence outside these directories is labeled separately.

## Review sheet

Leave the factual_correctness, source_support, language_appropriate, reviewer, and notes columns blank until you review each generated answer. Suggested values are yes/no/partial/not-applicable, with a short explanation. Check every claim against the displayed cited passage and compare completeness against the reference answer. Abstention is appropriate for unsupported questions; answering an answerable question does not itself establish correctness. Citation-format success is not source-support success.

Keep your completed review separate from these unreviewed originals and record who reviewed it and when. No human correctness rate has been calculated.

## Metrics and interpretation

Retrieval hit rate asks whether any expected physical page occurs in initial top-k. Recall@3 averages the fraction of expected pages found per answerable question, deduplicated by page. All-support@3 requires every expected page. Rewrites do not change these definitions. Unsupported questions have no target retrieval pages, so they are excluded from those denominators.

Generation summaries separately report answerable abstention and unsupported abstention, syntactic/reference validation failures, execution errors, and per-question wall-clock latency. Initialization/indexing/model loading are excluded from response latency. P95 is the nearest-rank empirical percentile. Errors are reported separately and never treated as abstentions or correct answers. Timing is machine-specific.

The held-out set was run once for retrieval and once for generation at source revision `4fdbdb8cd845959a02a3035e5841ef1e1c86fa5b`, after development. No prompt, retrieval parameter, reference label, or pipeline source was changed against held-out outcomes. Documentation and UI capture were prepared afterward; demo-only configuration explicitly selects the same fixed k=3 and forwards the local endpoint, while core/evaluator source remains unchanged. The published set is now visible and is not a fresh blind test for future tuning.

One explicit limitation is preserved: held10 retrieved Atlas pages 1/3/1 but missed expected Boreal page 2. The model did not rewrite or abstain and its cited answer omits Boreal's specific window/remedy. This is not counted as a correct answer; no automated or human semantic correctness score is assigned. It shows why perfect hit rate, zero abstention on answerable questions, and valid citations cannot establish answer completeness.
