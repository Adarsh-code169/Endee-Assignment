import os
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from backend.models import ChatRequest, ChatResponse
from backend.ingestion import extract_text_from_pdf, chunk_text
from backend.embeddings import embedding_model
from backend.vector_store import EndeeVectorStore
from backend.rag import RAGPipeline

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit

vector_store = None
rag_pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Init endee connection and RAG pipeline on startup."""
    global vector_store, rag_pipeline

    host = os.getenv("ENDEE_HOST", "localhost")
    port_str = os.getenv("ENDEE_PORT")
    port = int(port_str) if port_str else None
    groq_key = os.getenv("GROQ_API_KEY")

    if not groq_key:
        logger.warning("GROQ_API_KEY not set — chat won't work")

    vector_store = EndeeVectorStore(host=host, port=port)
    rag_pipeline = RAGPipeline(api_key=groq_key)
    logger.info("App ready")
    yield


app = FastAPI(title="Endee RAG API", version="1.0.0", lifespan=lifespan)

# allow frontend to call the API from a different port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF — extracts text, chunks it, embeds, and stores in Endee."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files supported")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    logger.info(f"Upload: '{file.filename}' ({len(content) / 1024:.1f} KB)")

    # extract → chunk → embed → store
    pages = extract_text_from_pdf(content, file.filename)
    if not pages:
        raise HTTPException(status_code=400, detail="No text found in PDF")

    chunks = chunk_text(pages)
    texts = [c["text"] for c in chunks]
    embeddings = embedding_model.generate_batch(texts)

    success = vector_store.insert(embeddings, chunks)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store in Endee")

    return {"message": f"Processed {len(chunks)} chunks from {file.filename}", "chunks": len(chunks)}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Ask a question — embeds query, searches Endee, generates answer with citations."""
    query_vec = embedding_model.generate(request.message)
    if not query_vec:
        raise HTTPException(status_code=400, detail="Couldn't process your query")

    results = vector_store.search(query_vec, top_k=5)
    response = rag_pipeline.generate_answer(request.message, results)
    return response


@app.get("/health")
def health():
    return {"status": "ok"}
