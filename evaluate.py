"""Page retrieval and generation diagnostics; no automatic correctness judgments."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time

from core import ROOT, Assistant, load_index, validate_index_manifest, GENERATION_SETTINGS


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def source_revision():
    directory = Path(__file__).resolve().parent
    result = subprocess.run(['git', '-C', str(directory), 'rev-parse', 'HEAD'], capture_output=True, text=True)
    status = subprocess.run(['git', '-C', str(directory), 'status', '--porcelain', '--', 'core.py', 'evaluate.py', 'evaluation/build_synthetic.py', 'evaluation/synthetic_v1'], capture_output=True, text=True)
    return {'git_commit': result.stdout.strip() if result.returncode == 0 else None,
            'evaluated_source_dirty': bool(status.stdout.strip()),
            'source_sha256': {name: hashlib.sha256((directory/name).read_bytes()).hexdigest()
                              for name in ('core.py', 'evaluate.py')}}


def run(dataset, root=ROOT, k=4, output=None, retrieval_only=False):
    if k < 1:
        raise ValueError('k must be at least 1.')
    dataset = Path(dataset)
    rows = [json.loads(line) for line in dataset.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not rows or len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Provide a nonempty dataset with unique question IDs.')
    for row in rows:
        if row.get('verified') is not True:
            raise ValueError('Rows need verified=true and an explicit label provenance after source verification.')
        if row['answerable'] and not row.get('sources'):
            raise ValueError('Answerable rows require verified source pages.')
        if not row['answerable'] and row.get('sources'):
            raise ValueError('Unsupported rows must not list supporting pages.')
    manifest = validate_index_manifest(root)
    output = Path(output or ROOT/'results')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output directory is not empty; choose a fresh directory to preserve prior results.')
    output.mkdir(parents=True, exist_ok=True)
    initialized = time.perf_counter()
    if retrieval_only:
        retriever = load_index(root).as_retriever(search_kwargs={'k': k})
        model = None
    else:
        assistant = Assistant(root, k)
        model = assistant.llm.metadata
    initialization_seconds = time.perf_counter() - initialized
    provenance = {
        'started_utc': datetime.now(timezone.utc).isoformat(), 'dataset_file': dataset.name,
        'dataset_sha256': hashlib.sha256(dataset.read_bytes()).hexdigest(),
        'corpus_version': sorted({row.get('corpus_version', 'not specified') for row in rows}),
        'splits': sorted({row.get('split', 'not specified') for row in rows}),
        'k': k, 'indexed_chunks': manifest.get('chunks'), 'index_manifest': manifest,
        'mode': 'retrieval only' if retrieval_only else 'retrieval and generation',
        'model': model, 'generation_settings': None if retrieval_only else GENERATION_SETTINGS,
        'initialization_seconds': initialization_seconds, 'python': platform.python_version(),
        'packages': {name: importlib.metadata.version(name) for name in
                     ('langchain-core', 'langgraph', 'sentence-transformers', 'pypdf', 'numpy')},
        'seed': 'No request seed; temperature=0 is not a guarantee of deterministic inference.',
        'latency_definition': 'Per-question wall time; includes retrieval/check/rewrite/generation, excludes initialization/indexing.',
        'human_correctness': 'not evaluated', **source_revision()}
    (output/'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    results = []
    for row in rows:
        started = time.perf_counter()
        try:
            if retrieval_only:
                passages = [dict(d.metadata, text=d.page_content) for d in retriever.invoke(row['question'])]
                result = {'initial_passages': passages, 'passages': passages}
            else:
                result = assistant.ask(row['question'])
            result['seconds'] = time.perf_counter() - started
            retrieved = {(p['filename'], p['page']) for p in result['initial_passages']}
            expected = {(s['filename'], s['page']) for s in row.get('sources', [])}
            hits = len(expected & retrieved)
            entry = dict(row, output=result, hit_at_k=bool(hits) if expected else None,
                         recall_at_k=hits/len(expected) if expected else None,
                         all_support_at_k=expected <= retrieved if expected else None, error=None)
        except (RuntimeError, ValueError, OSError) as error:
            # Preserve errors separately; they are neither correct answers nor abstentions.
            entry = dict(row, output={'seconds': time.perf_counter()-started}, hit_at_k=None,
                         recall_at_k=None, all_support_at_k=None, error=type(error).__name__)
        results.append(entry)
        (output/'answers.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in results), encoding='utf-8')
        print(f"{row['id']}: {'ERROR '+entry['error'] if entry['error'] else 'complete'}", flush=True)
    successful = [r for r in results if not r['error']]
    answerable = [r for r in successful if r['answerable']]
    unanswerable = [r for r in successful if not r['answerable']]
    mean = lambda values: statistics.mean(values) if values else None
    latencies = sorted(r['output']['seconds'] for r in successful)
    import math
    summary = {
        'n': len(rows), 'completed': len(successful), 'errors': len(rows)-len(successful),
        'answerable_n': len(answerable), 'unanswerable_n': len(unanswerable), 'k': k,
        'indexed_chunks': manifest.get('chunks'),
        'retrieval_hit_rate': mean([r['hit_at_k'] for r in answerable]),
        'recall_at_k': mean([r['recall_at_k'] for r in answerable]),
        'all_support_at_k': mean([r['all_support_at_k'] for r in answerable]),
        'answerable_abstentions': sum(r['output']['abstained'] for r in answerable) if not retrieval_only else None,
        'unanswerable_abstentions': sum(r['output']['abstained'] for r in unanswerable) if not retrieval_only else None,
        'answerable_abstention_rate': mean([r['output']['abstained'] for r in answerable]) if not retrieval_only else None,
        'unanswerable_abstention_accuracy': mean([r['output']['abstained'] for r in unanswerable]) if not retrieval_only else None,
        'citation_validation_failures': sum(r['output']['citation_valid'] is False for r in successful) if not retrieval_only else None,
        'mean_response_seconds': mean(latencies),
        'median_response_seconds': statistics.median(latencies) if latencies else None,
        'p95_response_seconds': latencies[math.ceil(.95*len(latencies))-1] if latencies else None,
        'answer_correctness': 'not human evaluated', 'preliminary': True,
        'metric_denominator': 'Successful questions only; errors are reported separately; retrieval uses initial top-k.'}
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    write_csv(output/'summary.csv', [summary])
    write_csv(output/'review.csv', [
        {'id': r['id'], 'question': r['question'], 'answerable': r['answerable'],
         'reference_answer': r.get('reference_answer', ''), 'expected_sources': json.dumps(r.get('sources', []), ensure_ascii=False),
         'answer': r['output'].get('answer', ''), 'citations': json.dumps(r['output'].get('claims', []), ensure_ascii=False),
         'factual_correctness': '', 'source_support': '', 'language_appropriate': '', 'reviewer': '', 'notes': ''}
        for r in results])
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dataset', type=Path)
    parser.add_argument('--k', type=int, default=4)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--retrieval-only', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(args.dataset, root=args.root, k=args.k, output=args.output, retrieval_only=args.retrieval_only), indent=2))
