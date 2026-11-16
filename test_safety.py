"""Deterministic regression checks; stubbed answers are not inference evidence."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from core import Assistant, indexing_configuration, load_index, validate_index_manifest
from evaluate import run


class Chain:
    def __init__(self, text): self.text = text
    def invoke(self, _): return self.text


def claim(text='A supported claim.', page=2):
    return {'text': text, 'sources': [{'filename': 'notes.pdf', 'page': page}]}


class SafetyTests(unittest.TestCase):
    def result(self, value, relevant=True):
        assistant = object.__new__(Assistant)
        assistant.chain = Chain(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False))
        return assistant.answer({'relevant': relevant, 'question': 'test', 'passages': [
            {'filename': 'notes.pdf', 'page': 2, 'text': 'fixture passage'},
            {'filename': 'notes.pdf', 'page': 3, 'text': 'second fixture passage'}]})

    def test_valid_page(self):
        result = self.result({'claims': [claim()]})
        self.assertFalse(result['abstained'])
        self.assertTrue(result['citation_valid'])
        self.assertIn('[notes.pdf, p. 2]', result['answer'])

    def test_mixed_cited_uncited_claims(self):
        result = self.result({'claims': [claim(), {'text': 'An uncited claim.', 'sources': []}]})
        self.assertTrue(result['abstained'])
        self.assertFalse(result['citation_valid'])
        self.assertEqual(result['claims'], [])

    def test_original_valid_citation_then_uncited_sentence(self):
        self.assertTrue(self.result('A fact [notes.pdf, p. 2]. An unsupported additional sentence.')['abstained'])

    def test_json_then_uncited_prose(self):
        self.assertTrue(self.result(json.dumps({'claims': [claim()]}) + '\nUncited conclusion.')['abstained'])

    def test_multiple_sentences_in_one_claim(self):
        self.assertTrue(self.result({'claims': [claim('First fact. Another unsupported claim.') ]})['abstained'])

    def test_multiple_separately_referenced_claims(self):
        result = self.result({'claims': [claim('First fact.'), claim('A second fact.', 3)]})
        self.assertFalse(result['abstained'])
        self.assertEqual(len(result['claims']), 2)
        self.assertIn('[notes.pdf, p. 3]', result['answer'])

    def test_invented_page(self):
        self.assertFalse(self.result({'claims': [claim(page=9)]})['citation_valid'])

    def test_invented_filename(self):
        item = claim()
        item['sources'][0]['filename'] = 'invented.pdf'
        self.assertTrue(self.result({'claims': [item]})['abstained'])

    def test_french_claims(self):
        self.assertFalse(self.result({'claims': [claim('La mitose produit deux cellules filles.'), claim('Le document décrit aussi la photosynthèse.', 3)]})['abstained'])

    def test_french_uncited_claim_rejected(self):
        self.assertTrue(self.result({'claims': [claim('Un fait cité.'), {'text': 'Une conclusion sans source.', 'sources': []}]})['abstained'])

    def test_model_abstention_is_not_validation_failure(self):
        result = self.result({'abstain': True})
        self.assertTrue(result['abstained'])
        self.assertIsNone(result['citation_valid'])
        self.assertEqual(result['abstention_reason'], 'model')

    def test_insufficient_evidence(self):
        self.assertEqual(self.result('unused', False)['abstention_reason'], 'insufficient_evidence')

    def test_boolean_page_rejected(self):
        self.assertTrue(self.result({'claims': [claim(page=True)]})['abstained'])

    def test_extra_uncited_text_key_rejected(self):
        self.assertTrue(self.result({'claims': [claim()], 'conclusion': 'No source.'})['abstained'])

    def test_invalid_k(self):
        with self.assertRaisesRegex(ValueError, 'k must be at least 1'):
            Assistant(k=0)

    def test_missing_index(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'No index found'):
                Assistant(Path(directory))


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'index').mkdir()
        (self.root/'index'/'vectors.json').write_text('{}')
        self.manifest = {'schema_version': 2, 'configuration': indexing_configuration(), 'documents': {}, 'chunks': 36}

    def write(self):
        (self.root/'index'/'manifest.json').write_text(json.dumps(self.manifest))

    def assert_both_paths_reject(self, message):
        data = self.root/'questions.jsonl'
        data.write_text(json.dumps({'id': 'fixture', 'question': 'test', 'verified': True, 'answerable': False, 'sources': []})+'\n')
        with patch('core.LocalEmbeddings') as embeddings, patch('core.LocalLLM') as model:
            with self.assertRaisesRegex(ValueError, message):
                Assistant(self.root)
            with self.assertRaisesRegex(ValueError, message):
                run(data, root=self.root, retrieval_only=True, output=self.root/'output')
            embeddings.assert_not_called()
            model.assert_not_called()

    def test_compatible_manifest_loads_index(self):
        self.write()
        with patch('core.LocalEmbeddings') as embeddings, patch('core.InMemoryVectorStore.load', return_value='store') as loader:
            self.assertEqual(load_index(self.root), 'store')
            loader.assert_called_once()
            embeddings.assert_called_once()

    def test_compatible_assistant(self):
        self.write()
        with patch('core.LocalEmbeddings'), patch('core.InMemoryVectorStore.load', return_value=Mock()), patch('core.LocalLLM'):
            self.assertIsNotNone(Assistant(self.root).graph)

    def test_missing_manifest(self):
        self.assert_both_paths_reject('manifest.*Reindex')

    def test_incompatible_embedding(self):
        self.manifest['configuration']['embedding_model'] = 'different-model'
        self.write()
        self.assert_both_paths_reject('incompatible.*Reindex')

    def test_incompatible_chunk_size(self):
        self.manifest['configuration']['chunk_size'] += 1
        self.write()
        self.assert_both_paths_reject('incompatible.*Reindex')

    def test_incompatible_overlap(self):
        self.manifest['configuration']['chunk_overlap'] = 0
        self.write()
        self.assert_both_paths_reject('incompatible.*Reindex')

    def test_legacy_manifest(self):
        self.manifest = {'_embedding': indexing_configuration()['embedding_model'], '_chunk': '900/150/v1'}
        self.write()
        self.assert_both_paths_reject('incompatible.*Reindex')

    def test_corrupt_manifest(self):
        (self.root/'index'/'manifest.json').write_text('{not json')
        self.assert_both_paths_reject('manifest.*Reindex')


if __name__ == '__main__':
    unittest.main()
