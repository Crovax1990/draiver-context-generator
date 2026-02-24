import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config

class TestOllamaEmbeddings(unittest.TestCase):
    def setUp(self):
        # Fake context file
        self.context_path = Path("tests/fake_context.md")
        self.context_path.write_text("# Test Context\n> **Fonte:** `test.pdf`\nContent here.", encoding="utf-8")

    def tearDown(self):
        if self.context_path.exists():
            self.context_path.unlink()

    @patch("src.rag_engine.OllamaEmbeddings")
    @patch("src.rag_engine.FAISS")
    @patch("src.rag_engine.TextLoader")
    def test_build_vectorstore_uses_ollama(self, mock_loader, mock_faiss, mock_ollama_class):
        """
        TDD Step 1: Verify that build_vectorstore uses OllamaEmbeddings 
        with the correct model and URL from config.
        """
        # Mocking the dependency chain
        mock_loader.return_value.load.return_value = [MagicMock(page_content="test", metadata={})]
        
        # Import here to trigger the imports in rag_engine
        from src.rag_engine import build_vectorstore
        
        # Action
        build_vectorstore(self.context_path)
        
        # Assertions
        # 1. Check if OllamaEmbeddings was initialized
        self.assertTrue(mock_ollama_class.called, "OllamaEmbeddings was NOT called")
        
        # 2. Check if it was called with parameters from config
        args, kwargs = mock_ollama_class.call_args
        self.assertEqual(kwargs.get("model"), config.OLLAMA_EMBEDDING_MODEL)
        self.assertEqual(kwargs.get("base_url"), config.OLLAMA_BASE_URL)

if __name__ == "__main__":
    unittest.main()
