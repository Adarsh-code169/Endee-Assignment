import os
import logging
from groq import Groq
from typing import List, Dict

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "llama-3.1-8b-instant"
LLM_TEMPERATURE = 0.3
MAX_TOKENS = 1024


class RAGPipeline:
    """Takes user query + retrieved context and generates a grounded answer using Groq."""

    def __init__(self, api_key: str, model: str = None):
        self.client = Groq(api_key=api_key)
        self.model = model or os.getenv("GROQ_MODEL", DEFAULT_MODEL)
        logger.info(f"RAG pipeline using model: {self.model}")

    def generate_answer(self, query: str, context: List[Dict]) -> Dict:
        """Generate an answer based on retrieved document chunks."""

        # if endee returned nothing, don't bother calling the LLM
        if not context:
            return {
                "answer": "I couldn't find relevant info in the uploaded documents. Try uploading a PDF on this topic first.",
                "citations": []
            }

        # format context with source labels so the LLM can cite them
        context_str = "\n\n".join([
            f"Source [{i+1}]: {item['text']} (File: {item['metadata'].get('filename')}, Page: {item['metadata'].get('page_number')})"
            for i, item in enumerate(context)
        ])

        system_prompt = (
            "You are a research assistant using RAG. "
            "Answer based only on the provided context. "
            "If the answer isn't in the context, say so. "
            "Cite sources like [Source 1]."
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {query}"}
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=MAX_TOKENS,
                top_p=1
            )
            answer = completion.choices[0].message.content
            return {"answer": answer, "citations": [c["metadata"] for c in context]}
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return {"answer": "Sorry, something went wrong while generating the answer. Please try again.", "citations": []}
