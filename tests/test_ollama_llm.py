import unittest
from unittest.mock import MagicMock
from langchain_ollama import ChatOllama
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from src.lesson_parser import LessonPlan
from src.rag_engine import SlideContent

class TestOllamaLLM(unittest.TestCase):
    def test_llm_initialization(self):
        """Verify that ChatOllama initializes with the correct model and parameters."""
        llm = ChatOllama(
            model=config.OLLAMA_LLM_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=config.LLM_TEMPERATURE,
            format="json"  # Enforce JSON mode for structured output if supported
        )
        self.assertEqual(llm.model, config.OLLAMA_LLM_MODEL)
        self.assertEqual(llm.base_url, config.OLLAMA_BASE_URL)

    def test_structured_output_capability(self):
        """
        Check if with_structured_output works as expected. 
        Note: This requires Ollama running with gpt-oss:20b.
        """
        llm = ChatOllama(
            model=config.OLLAMA_LLM_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            format="json"
        )
        
        # This is a smoke test for the interface. 
        # In a real TDD environment, we'd run this against the actual Ollama.
        try:
            structured_llm = llm.with_structured_output(SlideContent)
            print("✅ ChatOllama supports with_structured_output interface")
        except Exception as e:
            self.fail(f"ChatOllama failing to provide structured output interface: {e}")

if __name__ == "__main__":
    unittest.main()
