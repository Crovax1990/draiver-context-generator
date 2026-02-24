# Piano di Implementazione: Generatore di Presentazioni RAG (Ostetricia)

Questo documento descrive l'architettura e le fasi di implementazione per il modulo di generazione automatica di presentazioni PowerPoint, basato su un piano didattico predefinito e un contesto testuale/visivo indicizzato.

---

## 1. Stack Tecnologico

Per implementare la pipeline di generazione in Python in modo robusto, utilizzeremo le seguenti librerie standard di settore:

| Componente | Libreria Consigliata | Scopo Principale |
| :--- | :--- | :--- |
| **Orchestrazione RAG** | `LangChain` o `LlamaIndex` | Gestione del retrieval dal contesto e connessione all'LLM. |
| **Data Validation** | `Pydantic` | Forzatura dell'LLM a restituire output in formato JSON rigido. |
| **Generazione Documenti** | `python-pptx` | Creazione programmatica e manipolazione dei file PowerPoint. |

---

## 2. Fasi di Sviluppo

### Fase 1: Parsing e Segmentazione (`piano_didattico.md`)
* Scrivere uno script di parsing per leggere `piano_didattico.md`.
* Suddividere il documento in 5 oggetti distinti rappresentanti le singole lezioni.
* Estrarre la "scaletta" (titoli e sotto-argomenti) per ciascuna lezione per guidare la generazione.

### Fase 2: Information Retrieval e Sintesi (Core Logico)
* Caricare il file `context.md` in un Vector Store in-memory frammentandolo in chunk.
* Salvare il "nome documento originale" nei metadati di ogni chunk.
* Interrogare l'LLM per ogni punto della scaletta richiedendo una sintesi.
* Utilizzare Pydantic per forzare l'output in un JSON con i campi: `titolo_slide`, `bullet_points`, `source_doc_name`.

### Fase 3: Logica di Matching delle Immagini
* Leggere il campo `source_doc_name` restituito dal JSON generato nella Fase 2.
* Scansionare la directory `images/` alla ricerca di file che matchano il pattern `[source_doc_name]_[numero].ext`.
* Selezionare in modo sequenziale la prima immagine pertinente e non ancora utilizzata per popolare la slide.

### Fase 4: Rendering e Salvataggio (`python-pptx`)
* Creare un file `template.pptx` con un layout Master predefinito (Titolo, Corpo Testo, Immagine a destra).
* Avviare il loop di generazione iterando sulle 5 lezioni elaborate.
* Popolare le caselle di testo con i `bullet_points` e inserire le immagini associate calcolate nella Fase 3.
* Salvare l'output in 5 file separati (es. `Lezione_1.pptx`, `Lezione_2.pptx`, ecc.).

---

## 3. Gestione dei Rischi e Best Practices

* **Prolissità dell'LLM:** Gli LLM tendono a generare muri di testo. È essenziale impostare direttive rigide nel prompt (es. "Massimo 4 bullet points, massimo 15 parole per bullet").
* **Deformazione Immagini:** Durante l'inserimento con `python-pptx`, definire solo una dimensione (es. `width`) per mantenere l'aspect ratio (proporzioni) originale ed evitare distorsioni.
* **Allucinazioni (Ambito Medico):** Impostare il parametro `temperature` dell'LLM a `0.0` per garantire che vengano utilizzate esclusivamente le informazioni presenti nel `context.md` di ostetricia.

---

## 4. Esempio Architetturale (Pseudo-Codice)

```python
from pptx import Presentation
from pptx.util import Inches

def crea_presentazione(lezione_data, template_path="template.pptx"):
    prs = Presentation(template_path)
    
    for slide_data in lezione_data.slides:
        # Selezione layout: Titolo + Contenuto + Immagine
        slide_layout = prs.slide_layouts[1] 
        slide = prs.slides.add_slide(slide_layout)
        
        # Inserimento Titolo
        slide.shapes.title.text = slide_data.titolo
        
        # Inserimento Bullet Points
        tf = slide.placeholders[1].text_frame
        for bullet in slide_data.bullet_points:
            p = tf.add_paragraph()
            p.text = bullet
            
        # Matching e Inserimento Immagine
        if slide_data.image_path:
            slide.shapes.add_picture(
                slide_data.image_path, 
                Inches(5), Inches(2), width=Inches(4)
            )
            
    prs.save(f"{lezione_data.titolo_lezione}.pptx")