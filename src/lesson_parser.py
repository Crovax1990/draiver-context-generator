"""
Draiver Context Generator – Lesson Plan Parser
Parses piano_didattico.md to extract the structure of the 5 lessons.
"""
import logging
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

import config

logger = logging.getLogger(__name__)

class SlideSpec(BaseModel):
    """Specifica di una singola slide da generare."""
    titolo: str = Field(description="Titolo della slide")
    argomenti: List[str] = Field(description="Lista di sotto-argomenti da trattare")

class LezioneSpec(BaseModel):
    """Specifica completa di una lezione."""
    numero: int = Field(description="Numero della lezione (1-5)")
    titolo: str = Field(description="Titolo della lezione")
    durata: str = Field(default="4 ore", description="Durata della lezione")
    obiettivi_formativi: List[str] = Field(description="Obiettivi formativi")
    scaletta: List[SlideSpec] = Field(description="Scaletta degli argomenti (almeno 3-6 voci)")
    esercizi: List[str] = Field(default_factory=list, description="Esercizi pratici")
    materiali: List[str] = Field(default_factory=list, description="Materiali e strumenti")

class LessonPlan(BaseModel):
    """Intero piano didattico composto da più lezioni."""
    lezioni: List[LezioneSpec] = Field(description="Elenco delle lezioni estratte dal piano")

def parse_piano_didattico(path: Path) -> List[LezioneSpec]:
    """
    Parses the markdown lesson plan using an LLM with structured output.
    """
    if not path.exists():
        raise FileNotFoundError(f"Lesson plan not found at {path}")

    logger.info("Parsing lesson plan from %s", path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    llm = ChatGoogleGenerativeAI(
        model=config.LLM_MODEL,
        temperature=0,
        google_api_key=config.GOOGLE_API_KEY
    )

    parser = PydanticOutputParser(pydantic_object=LessonPlan)

    prompt = ChatPromptTemplate.from_template(
        "Analizza il seguente piano didattico in formato Markdown ed estrai la struttura "
        "delle lezioni (titolo, obiettivi, scaletta argomenti, esercizi, materiali). "
        "Il piano contiene solitamente 5 lezioni principali.\n\n"
        "{format_instructions}\n\n"
        "PIANO DIDATTICO:\n{content}"
    )

    prompt_and_model = prompt | llm | parser

    output = prompt_and_model.invoke({
        "content": content,
        "format_instructions": parser.get_format_instructions()
    })

    logger.info("Successfully parsed %d lessons", len(output.lezioni))
    return output.lezioni

if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    try:
        lezioni = parse_piano_didattico(Path("output/piano_didattico.md"))
        for l in lezioni:
            print(f"Lezione {l.numero}: {l.titolo} ({len(l.scaletta)} slide in scaletta)")
    except Exception as e:
        print(f"Error: {e}")
