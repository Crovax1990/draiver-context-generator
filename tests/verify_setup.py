import sys
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import config
except ImportError:
    print("❌ Error: Could not import config.py. Make sure you are running the test from the project root.")
    sys.exit(1)

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

def verify_config_setup():
    print(f"\n--- Verifying Gemini Setup (from config.py) ---")
    
    api_key = config.GOOGLE_API_KEY
    if not api_key:
        print("❌ GOOGLE_API_KEY is not set in config.py or environment.")
        return False
    
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    
    # 1. Test LLM
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
    
    # 2. Test Embeddings
    embedding_model = config.EMBEDDING_MODEL
    print(f"\nVerifying Embeddings model: {embedding_model}...")
    emb_ok = False
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model, google_api_key=api_key)
        vector = embeddings.embed_query("Hi")
        print(f"✅ Embeddings verified! Vector size: {len(vector)}")
        emb_ok = True
    except Exception as e:
        print(f"❌ Embeddings verification failed for {embedding_model}: {e}")

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
