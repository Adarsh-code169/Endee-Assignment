import io
import logging
from pypdf import PdfReader
from typing import List, Dict

logger = logging.getLogger(__name__)

# chunk params — 500 chars with 50 overlap works well for MiniLM embeddings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def extract_text_from_pdf(file_content: bytes, filename: str) -> List[Dict]:
    """Extract text from each page of a PDF file."""
    reader = PdfReader(io.BytesIO(file_content))
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append({
                "text": text.strip(),
                "page_number": i + 1,
                "filename": filename
            })
        else:
            logger.warning(f"Skipping page {i+1} of '{filename}' — no text found")

    logger.info(f"Extracted {len(pages)}/{len(reader.pages)} pages from '{filename}'")
    return pages


def chunk_text(pages: List[Dict], chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict]:
    """Split page text into overlapping chunks for better retrieval."""
    chunks = []
    chunk_id = 0

    for page in pages:
        text = page["text"]
        start = 0

        # sliding window with overlap so we don't cut sentences mid-way
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append({
                "id": f"{page['filename']}_p{page['page_number']}_{chunk_id}",
                "text": text[start:end],
                "metadata": {
                    "filename": page["filename"],
                    "page_number": page["page_number"],
                    "chunk_id": chunk_id
                }
            })
            chunk_id += 1
            start += (chunk_size - overlap)

    logger.info(f"Created {len(chunks)} chunks from {len(pages)} pages")
    return chunks
