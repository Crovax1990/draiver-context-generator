"""
Draiver Context Generator – RAG Engine
Handles indexing of context.md and generation of slide content.
"""
import logging
import re
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

import config

logger = logging.getLogger(__name__)

class SlideContent(BaseModel):
    """Output strutturato per una singola slide."""
    titolo_slide: str = Field(description="Titolo conciso della slide")
    bullet_points: List[str] = Field(
        description="Bullet points (max 6, max 15 parole ciascuno)",
        max_length=6
    )
    note_relatore: str = Field(
        description="Script parlato per il docente (3-6 frasi)"
    )
    source_doc_names: List[str] = Field(
        description="Nomi dei documenti sorgente utilizzati (es. dal contesto RAG)"
    )

def build_vectorstore(context_path: Path) -> FAISS:
    """
    Loads context.md, splits into chunks with source metadata, and builds a FAISS index.
    """
    logger.info("Building vector store from %s", context_path)
    
    # Load document
    loader = TextLoader(str(context_path), encoding="utf-8")
    documents = loader.load()
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.RAG_CHUNK_SIZE,
        chunk_overlap=config.RAG_CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    chunks = text_splitter.split_documents(documents)
    
    # Enrich metadata with source document names
    # Context.md lines often look like: > **Fonte:** `DocName.pdf` | **Pagine:** N
    source_pattern = re.compile(r"Fonte:\*\* `([^`]+)`")
    
    current_source = "Unknown"
    for chunk in chunks:
        # Search for source in the chunk content
        match = source_pattern.search(chunk.page_content)
        if match:
            current_source = match.group(1).replace(".pdf", "").replace(".docx", "").replace(".pptx", "")
        
        chunk.metadata["source_doc_name"] = current_source
        
    embeddings = GoogleGenerativeAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        google_api_key=config.GOOGLE_API_KEY
    )
    
    vectorstore = FAISS.from_documents(chunks, embeddings)
    logger.info("Vector store built with %d chunks", len(chunks))
    return vectorstore

def generate_slide_content(
    retriever, 
    topic: str, 
    lesson_title: str
) -> SlideContent:
    """
    Retrieves context and generates structured slide content via LLM.
    """
    llm = ChatGoogleGenerativeAI(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        google_api_key=config.GOOGLE_API_KEY
    )
    
    structured_llm = llm.with_structured_output(SlideContent)
    
    prompt = ChatPromptTemplate.from_template("""
Sei un esperto di formazione ostetrica. Genera il contenuto per una slide 
di presentazione PowerPoint professionale.

ARGOMENTO DA TRATTARE: {topic}
TITOLO LEZIONE: {lesson_title}

CONTESTO RAG (estratti dai documenti di riferimento):
{context}

REGOLE RIGOROSE:
- Massimo 6 bullet points per slide
- Massimo 15 parole per bullet point  
- Le note del relatore devono essere 3-6 frasi di script parlato (quello che il docente deve DIRE)
- Usa SOLO informazioni presenti nel contesto fornito. Se non trovi nulla, indica concetti generali ma coerenti.
- Nelle note, cita esplicitamente il documento sorgente se pertinente.
- Terminologia tecnica italiana corretta.

Rispondi in formato JSON strutturato.
""")

    def format_docs(docs):
        return "\n\n".join([
            f"--- ESTRATTO DA {doc.metadata.get('source_doc_name', 'Unknown')} ---\n{doc.page_content}" 
            for doc in docs
        ])

    chain = (
        {"context": retriever | format_docs, "topic": RunnablePassthrough(), "lesson_title": RunnablePassthrough()}
        | prompt
        | structured_llm
    )
    
    return chain.invoke({"topic": topic, "lesson_title": lesson_title})

if __name__ == "__main__":
    # Quick test if context exists
    logging.basicConfig(level=logging.INFO)
    c_path = Path("output/context.md")
    if c_path.exists():
        vs = build_vectorstore(c_path)
        retriever = vs.as_retriever(search_kwargs={"k": config.RAG_RETRIEVAL_K})
        content = generate_slide_content(retriever, "Ruolo dell'ostetrica nel BRO", "Lezione 1")
        print(content.model_dump_json(indent=2))
