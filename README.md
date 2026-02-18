# 🚀 Draiver Context Generator

Un potente convertitore locale basato su **Docling (IBM)** per trasformare dispense universitarie e documenti (PDF, DOCX, PPTX, TXT) in basi di conoscenza Markdown strutturate, pronte per essere consumate da agenti AI o sistemi RAG.

---

## ✨ Caratteristiche Principali

- **📄 Parsing Avanzato**: Sfrutta la tecnologia Docling per estrarre non solo testo, ma anche **tabelle, liste e intestazioni** mantenendo la gerarchia del documento.
- **🖼️ Estrazione Immagini**: Recupera automaticamente tutte le immagini dai documenti e le organizza in una cartella dedicata.
- **⚡ Elaborazione Parallela**: Supporto multi-threading (configurabile) per elaborare decine di documenti in pochi secondi sfruttando tutta la CPU.
- **📊 Audit Report**: Genera un report JSON dettagliato con lo stato di ogni documento, errori catturati, numero di pagine e warning tecnici.
- **🔄 Deduplicazione**: Script incluso per rimuovere immagini identiche caricate più volte negli stessi documenti.
- **📁 Flessibilità Output**: Modalità "per documento" (1:1) o "single" (un unico file aggregato con TOC).

---

## 🛠️ Setup

```bash
# 1. Crea e attiva un virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 2. Installa le dipendenze
pip install -r requirements.txt

# 3. Prepara i documenti
mkdir input
# Copia i tuoi file PDF, DOCX, PPTX, TXT nella cartella input/
```

---

## 🚀 Utilizzo

### Pipeline Principale (`main.py`)

Il comando principale esegue l'ingestion, la conversione e la generazione dell'output.

```bash
# Esecuzione standard (1:1 markdown, 2 thread paralleli)
python main.py

# Aggrega tutto in un unico file context.md
python main.py --mode single

# Aumenta le performance (es. 4 thread)
python main.py --threads 4

# Disabilita l'estrazione immagini
python main.py --no-images

# Personalizza i percorsi
python main.py --input ./my_docs --output ./my_knowledge_base
```

### Script di Deduplicazione Immagini

Docling spesso estrae la stessa immagine se questa compare più volte in un documento (o tra più documenti). Usa questo script per pulire la cartella di output:

```bash
# Solo anteprima (dry-run)
python scripts/deduplicate_images.py --dry-run

# Esecuzione effettiva (sposta i duplicati in output/images/duplicates)
python scripts/deduplicate_images.py
```

---

## 📜 Formato di Output

Ogni file Markdown generato include:
- **YAML Frontmatter**: Metadati (titolo, file sorgente, dimensioni, conteggio pagine/immagini, timestamp).
- **Contenuto Markdown**: Testo strutturato con supporto a tabelle e blocchi di codice.
- **Immagini**: Salvate in `output/images/` con naming coerente `<documento>_img_xxx.png`.

---

## 📊 Audit & Rapporti

Al termine di ogni esecuzione, troverai `output/audit_report.json`. Questo file è fondamentale per diagnosticare problemi su documenti complessi:
- **Status**: `success`, `partial` (estratto con warning) o `failed`.
- **Warnings**: Include messaggi di basso livello (es. errori OCR su singole pagine o `std::bad_alloc` su file giganti).
- **Stats**: Statistiche aggregate sull'intera sessione di elaborazione.

---

## 🏗️ Struttura del Progetto

```text
draiver-context-generator/
├── input/                  # Sorgenti (PDF, DOCX, PPTX, TXT)
├── output/                 # Markdown generati
│   ├── images/             # Immagini estratte
│   │   └── duplicates/     # Immagini rimosse dallo script deduplicator
│   └── audit_report.json   # Report dettagliato dell'ultima esecuzione
├── scripts/
│   └── deduplicate_images.py # Utility per la pulizia immagini
├── src/
│   ├── ingestion.py        # Scansione filesystem
│   ├── extraction.py       # Motore Docling + Parallelismo + Warning capture
│   ├── audit.py            # Logica di auditing thread-safe
│   └── output_writer.py    # Formattazione Markdown & Frontmatter
├── main.py                 # CLI principale
├── config.py               # Parametri globali e default
└── requirements.txt        # Dipendenze (docling, pillow, etc.)
```

---

## 🛡️ Supporto Formati

| Formato | Estensione | Note |
|:---|:---:|:---|
| **PDF** | `.pdf` | Supporto OCR integrale tramite Docling |
| **Word** | `.docx` | Preserva tabelle e formattazione |
| **PowerPoint** | `.pptx` | Ottimo per slides e diagrammi |
| **Text** | `.txt` | Conversione diretta |

---

*Powered by [Docling](https://github.com/DS4SD/docling)*
