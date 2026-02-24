import sys
import logging
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import config
    from src.utils import gemini_retry
except ImportError:
    print("❌ Error: Could not import config.py or src.utils. Make sure you are running the test from the project root.")
    sys.exit(1)

# Configure logging to see retry warnings
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s – %(message)s')

def verify_imports():
    print("--- Verifying Imports ---")
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        print("✅ langchain-google-genai is installed correctly.")
        return True
    except ImportError as e:
        print(f"❌ Error importing langchain-google-genai: {e}")
        print("Please run: pip install langchain-google-genai")
        return False

@gemini_retry(max_attempts=3)
def verify_config_setup():
    print(f"\n--- Verifying Gemini Setup (from config.py) ---")
    
    api_key = config.GOOGLE_API_KEY
    if not api_key:
        print("❌ GOOGLE_API_KEY is not set in config.py or environment.")
        return False
    
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_ollama import OllamaEmbeddings
    
    # 1. Test LLM (Still Gemini)
    model_name = config.LLM_MODEL
    print(f"Testing LLM model: {model_name}...")
    llm_ok = False
    try:
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
        response = llm.invoke("Hi")
        print(f"✅ LLM verified with model {model_name}!")
        llm_ok = True
    except Exception as e:
        print(f"❌ LLM verification failed for {model_name}: {e}")
    
    # 2. Test Embeddings (Now Ollama)
    print(f"\nVerifying Ollama Embeddings model: {config.OLLAMA_EMBEDDING_MODEL}...")
    emb_ok = False
    try:
        embeddings = OllamaEmbeddings(
            model=config.OLLAMA_EMBEDDING_MODEL, 
            base_url=config.OLLAMA_BASE_URL
        )
        vector = embeddings.embed_query("Hi")
        print(f"✅ Ollama Embeddings verified! Vector size: {len(vector)}")
        emb_ok = True
    except Exception as e:
        print(f"❌ Ollama Embeddings verification failed: {e}")
        print("💡 Make sure Ollama is running and the model is pulled: ollama pull qwen3-embedding")

    return llm_ok and emb_ok

if __name__ == "__main__":
    if verify_imports():
        success = verify_config_setup()
        if success:
            print("\n✨ Setup verification completed successfully!")
        else:
            print("\n⚠️ Setup verification failed. Please check the errors above.")
    else:
        print("\nSkipping configuration check due to missing imports.")
