# Intelligent Research Assistant — RAG with Endee Vector Database

A RAG-based research assistant that lets you upload academic PDFs and ask questions about them. It uses **Endee** as the vector database for semantic search and **Llama 3.1** (via Groq) for generating answers with page-level citations.

---

## Problem

Searching through long academic papers manually is slow. Keyword search doesn't understand context or intent. This project uses semantic search + RAG to give you precise, cited answers from your documents.

---

## Architecture

```
User (Streamlit UI)
    │
    ├── Upload PDF ──→ FastAPI /upload
    │                      │
    │                      ├── Extract text (pypdf)
    │                      ├── Chunk text (500 chars, 50 overlap)
    │                      ├── Generate embeddings (MiniLM)
    │                      └── Store in Endee
    │
    └── Ask Question ──→ FastAPI /chat
                             │
                             ├── Embed query (MiniLM)
                             ├── Search Endee (top 5 similar chunks)
                             └── Generate answer (Llama 3.1 via Groq)
                                  └── Return answer + citations
```

---

## How Endee is Used

Endee is the core vector database in this project. Here's what it does:

- **Stores** 384-dimensional embeddings for each document chunk
- **Indexes** vectors with metadata (filename, page number, chunk ID)
- **Searches** using cosine similarity to find the most relevant chunks for a query

I chose Endee over alternatives like Chroma because of its C++ backend — it's fast and lightweight with a clean REST API, no heavy SDK needed.

---

## Project Structure

```
├── backend/
│   ├── main.py            # FastAPI app + routes
│   ├── models.py          # request/response schemas
│   ├── ingestion.py       # PDF extraction + chunking
│   ├── embeddings.py      # sentence-transformers wrapper
│   ├── vector_store.py    # Endee client
│   └── rag.py             # RAG pipeline (context + LLM)
├── frontend/
│   └── app.py             # Streamlit chat UI
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── Makefile
├── .env.example
└── README.md
```

---

## Tech Stack

| Component | Tech |
|-----------|------|
| Vector DB | Endee |
| LLM | Llama 3.1 8B (Groq) |
| Embeddings | all-MiniLM-L6-v2 |
| Backend | FastAPI |
| Frontend | Streamlit |
| Containerization | Docker |

---

## Setup

### Prerequisites
- Docker
- Python 3.9+
- [Groq API key](https://console.groq.com/keys) (free)

### 1. Start Endee

```bash
git clone https://github.com/EndeeLabs/endee
cd endee
./install.sh --release --avx2
./run.sh
```

### 2. Clone this project

```bash
git clone <your-fork-url>
cd Endee-Assignment
cp .env.example .env
# edit .env and add your GROQ_API_KEY
```

### 3. Run with Docker (recommended)

```bash
docker-compose up --build
```

This starts both the backend (port 8000) and frontend (port 8501).

### 3b. Or run manually

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# terminal 1
uvicorn backend.main:app --reload --port 8000

# terminal 2
streamlit run frontend/app.py
```

### 4. Use it

1. Open `http://localhost:8501`
2. Upload a PDF in the sidebar
3. Ask questions in the chat

---

## API

| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/upload` | POST | Upload + process a PDF |
| `/chat` | POST | Ask a question, get answer + citations |
| `/health` | GET | Health check |

---

## Limitations

- Only works with text-based PDFs (no OCR for scanned docs)
- Single collection — all docs go in one place
- Chat history resets on page reload
- Best results with English text
