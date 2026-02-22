"""
Draiver Context Generator – PPTX Generation CLI
Orchestrates the full pipeline to generate PowerPoint presentations.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Set

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).parent / "src"))

import config
from src.lesson_parser import parse_piano_didattico
from src.rag_engine import build_vectorstore, generate_slide_content
from src.image_matcher import match_images
from src.pptx_renderer import PPTXRenderer

def _setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
        datefmt="%H:%M:%S",
    )

def main():
    _setup_logging()
    logger = logging.getLogger("generate_pptx")
    
    parser = argparse.ArgumentParser(description="Gera presentazioni PowerPoint via RAG (Gemini)")
    parser.add_argument("--context", type=Path, default=config.OUTPUT_DIR / "context.md", help="Path al file context.md")
    parser.add_argument("--plan", type=Path, default=config.OUTPUT_DIR / "piano_didattico.md", help="Path al file piano_didattico.md")
    parser.add_argument("--output", type=Path, default=config.PPTX_OUTPUT_DIR, help="Directory di output per i PPTX")
    parser.add_argument("--api-key", type=str, default=config.GOOGLE_API_KEY, help="Google API Key")
    
    args = parser.parse_args()
    
    if not args.api_key:
        logger.error("ERRORE: Google API Key non trovata. Imposta GOOGLE_API_KEY nell'ambiente o usa --api-key.")
        sys.exit(1)
    
    # Update config with provided API key
    config.GOOGLE_API_KEY = args.api_key
    
    logger.info("=== Inizio Generazione Presentazioni RAG ===")
    
    # 1. Parsing Piano Didattico
    try:
        lezioni = parse_piano_didattico(args.plan)
    except Exception as e:
        logger.error("Errore nel parsing del piano didattico: %s", e)
        sys.exit(1)
        
    # 2. Indexing Context
    try:
        vectorstore = build_vectorstore(args.context)
        retriever = vectorstore.as_retriever(search_kwargs={"k": config.RAG_RETRIEVAL_K})
    except Exception as e:
        logger.error("Errore nell'indicizzazione del contesto: %s", e)
        sys.exit(1)
        
    # 3. Preparazione Immagini e Renderer Completo
    images_dir = config.OUTPUT_DIR / config.IMAGES_SUBDIR
    used_images: Set[str] = set()
    
    master_renderer = PPTXRenderer(config.TEMPLATE_PATH)
    master_renderer.add_title_slide(
        "Ostetrica di Comunità e del Percorso Nascita",
        "Formazione per Ostetriche - Percorso in 5 Lezioni"
    )
    
    # 4. Generazione per ogni Lezione
    for lezione in lezioni:
        logger.info("Elaborazione Lezione %d: %s", lezione.numero, lezione.titolo)
        
        # Renderer individuale per la lezione
        lesson_renderer = PPTXRenderer(config.TEMPLATE_PATH)
        lesson_renderer.add_title_slide(
            f"Lezione {lezione.numero}: {lezione.titolo}",
            f"Durata stimata: {lezione.durata}"
        )
        
        # Slide Obiettivi
        master_renderer.add_section_header(f"Lezione {lezione.numero}: {lezione.titolo}")
        
        # Generazione slide dalla scaletta
        for slide_spec in lezione.scaletta:
            logger.info("  Generazione slide: %s", slide_spec.titolo)
            
            # RAG Generation
            topic_query = f"{slide_spec.titolo}: {', '.join(slide_spec.argomenti)}"
            slide_data = generate_slide_content(retriever, topic_query, lezione.titolo)
            
            # Image Matching
            img_path = match_images(slide_data.source_doc_names, images_dir, used_images)
            
            # Rendering
            lesson_renderer.add_content_slide(slide_data, img_path)
            master_renderer.add_content_slide(slide_data, img_path)
            
        # Slide Esercizi/Materiali per la lezione individuale
        if lezione.esercizi:
            lesson_renderer.add_final_slide("Esercizi Pratici", lezione.esercizi)
        
        # Salvataggio lezione individuale
        lesson_filename = args.output / f"Lezione_{lezione.numero}_{lezione.titolo.replace(' ', '_')}.pptx"
        lesson_renderer.save(lesson_filename)
        
    # 5. Salvataggio Master Deck
    master_filename = args.output / "Corso_Completo_Ostetricia_Comunita.pptx"
    master_renderer.save(master_filename)
    
    logger.info("=== Generazione Completata con Successo ===")
    logger.info("File generati in: %s", args.output)

if __name__ == "__main__":
    main()
