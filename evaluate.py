"""No automatic answer correctness judge. Source labels must be manually verified."""
import argparse, csv, json, statistics
from pathlib import Path
from core import ROOT, Assistant, LocalEmbeddings, InMemoryVectorStore

def run(dataset,root=ROOT,k=4,output=None,retrieval_only=False):
    if k < 1: raise ValueError('k must be at least 1.')
    rows=[json.loads(line) for line in Path(dataset).read_text(encoding='utf-8').splitlines() if line.strip()]
    for row in rows:
        if row.get('verified') is not True: raise ValueError('Every row needs verified=true after manual source verification.')
        if row['answerable'] and not row.get('sources'): raise ValueError('Answerable rows require verified source pages.')
    if retrieval_only:
        path=Path(root)/'index'/'vectors.json'
        if not path.is_file(): raise ValueError('No index found. Run core.py index first.')
        retriever=InMemoryVectorStore.load(str(path),LocalEmbeddings()).as_retriever(search_kwargs={'k':k})
    else:
        assistant=Assistant(root,k)
    results=[]
    output=Path(output or ROOT/'results'); output.mkdir(parents=True,exist_ok=True)
    for row in rows:
        if retrieval_only:
            passages=[dict(d.metadata,text=d.page_content) for d in retriever.invoke(row['question'])]
            result={'initial_passages':passages}
        else:
            result=assistant.ask(row['question'])
        expected={(s['filename'],s['page']) for s in row.get('sources',[])}
        retrieved={(p['filename'],p['page']) for p in result['initial_passages']}
        hits=len(expected & retrieved)
        results.append(dict(row,**{'output':result,'hit_at_k':bool(hits) if expected else None,'recall_at_k':hits/len(expected) if expected else None}))
        (output/'raw.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in results)+'\n',encoding='utf-8')
    answerable=[r for r in results if r['answerable']]; unanswerable=[r for r in results if not r['answerable']]
    summary={'dataset':str(dataset),'n':len(results),'answerable_n':len(answerable),'unanswerable_n':len(unanswerable),'k':k,
             'retrieval_hit_rate':statistics.mean(r['hit_at_k'] for r in answerable) if answerable else '',
             'recall_at_k':statistics.mean(r['recall_at_k'] for r in answerable) if answerable else '',
             'unanswerable_abstention_accuracy':statistics.mean(r['output']['abstained'] for r in unanswerable) if unanswerable and not retrieval_only else '',
             'answerable_abstention_rate':statistics.mean(r['output']['abstained'] for r in answerable) if answerable and not retrieval_only else '',
             'mean_response_seconds':statistics.mean(r['output']['seconds'] for r in results) if results and not retrieval_only else '',
             'mode':'retrieval only' if retrieval_only else 'retrieval and generation',
             'answer_correctness':'not evaluated' if retrieval_only else 'not human evaluated',
             'relevance_check':'not executed' if retrieval_only else 'automatic local LLM'}
    with (output/'summary.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=summary); writer.writeheader(); writer.writerow(summary)
    return summary
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('dataset'); parser.add_argument('--k',type=int,default=4)
    parser.add_argument('--root',type=Path,default=ROOT); parser.add_argument('--output',type=Path)
    parser.add_argument('--retrieval-only',action='store_true'); args=parser.parse_args()
    print(json.dumps(run(args.dataset,root=args.root,k=args.k,output=args.output,retrieval_only=args.retrieval_only),indent=2))
