"""Synthetic fixture and metric checks; no model output is judged correct here."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from langchain_core.documents import Document
from core import indexing_configuration, PyPDFLoader
from evaluate import run


class EvaluationTests(unittest.TestCase):
    def test_authored_corpus_and_split_integrity(self):
        base = Path(__file__).resolve().parent/'evaluation'/'synthetic_v1'
        corpus = json.loads((base/'corpus.json').read_text(encoding='utf-8'))
        pages = PyPDFLoader(str(base/'meridian.pdf')).load()
        self.assertEqual(len(pages), 18)
        sets = []
        for filename, count in [('development.jsonl',12),('held_out.jsonl',16)]:
            rows = [json.loads(line) for line in (base/filename).read_text(encoding='utf-8').splitlines()]
            self.assertEqual(len(rows),count)
            sets.append({row['id'] for row in rows})
            for row in rows:
                for source in row['sources']:
                    self.assertIn(source['page'], range(1,19))
                if row['support_quote']:
                    # Physical extraction checks the page labels, not generated-answer correctness.
                    self.assertTrue(any(row['support_quote'] in ' '.join(pages[source['page']-1].page_content.split()) for source in row['sources']), row['id'])
        self.assertFalse(sets[0] & sets[1])
        self.assertTrue(corpus['synthetic'])

    def test_retrieval_metrics_deduplicate_pages_and_require_all_support(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'index').mkdir()
            (root/'index'/'manifest.json').write_text(json.dumps({'schema_version':2, 'configuration':indexing_configuration(), 'chunks':36}))
            rows = [{'id':'multi','question':'fixture','answerable':True,'verified':True,
                     'sources':[{'filename':'fixture.pdf','page':1},{'filename':'fixture.pdf','page':2}]}]
            data = root/'dataset.jsonl'
            data.write_text(json.dumps(rows[0])+'\n')
            store = Mock()
            store.as_retriever.return_value.invoke.return_value = [
                Document(page_content='first chunk',metadata={'filename':'fixture.pdf','page':1}),
                Document(page_content='second chunk same page',metadata={'filename':'fixture.pdf','page':1})]
            with patch('evaluate.load_index',return_value=store):
                summary = run(data, root=root, k=2, output=root/'output', retrieval_only=True)
            self.assertEqual(summary['retrieval_hit_rate'],1)
            self.assertEqual(summary['recall_at_k'],.5)
            self.assertEqual(summary['all_support_at_k'],0)
            self.assertIsNone(summary['answerable_abstentions'])
            review = (root/'output'/'review.csv').read_text(encoding='utf-8')
            self.assertIn('factual_correctness,source_support',review)


if __name__ == '__main__':
    unittest.main()
