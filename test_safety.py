"""Deterministic citation/abstention tests; these do not measure Qwen accuracy."""
import unittest
import tempfile
from pathlib import Path
from core import Assistant

class Chain:
    def __init__(self,text): self.text=text
    def invoke(self,_): return self.text

class SafetyTests(unittest.TestCase):
    def result(self,text,relevant=True):
        assistant=object.__new__(Assistant); assistant.chain=Chain(text)
        return assistant.answer({'relevant':relevant,'question':'test','passages':[{'filename':'notes.pdf','page':2,'text':'test'}]})
    def test_valid_page(self):
        self.assertFalse(self.result('A fact [notes.pdf, p. 2]')['abstained'])
    def test_invented_page(self):
        self.assertTrue(self.result('A fact [notes.pdf, p. 9]')['abstained'])
    def test_missing_citation(self):
        self.assertTrue(self.result('An unsupported fact')['abstained'])
    def test_insufficient_evidence(self):
        self.assertTrue(self.result('anything',False)['abstained'])
    def test_missing_index_reports_setup_before_model_initialization(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'No index found'):
                Assistant(Path(directory))
    def test_invalid_k(self):
        with self.assertRaisesRegex(ValueError, 'k must be at least 1'):
            Assistant(k=0)

if __name__=='__main__': unittest.main()
