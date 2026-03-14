import logging
import requests
from typing import List, Dict

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10  # seconds


class EndeeVectorStore:
    """Client for the Endee vector database — handles insert and search operations."""

    def __init__(self, host: str = "localhost", port: int = 8080, collection: str = "research_papers"):
        self.base_url = f"http://{host}:{port}"
        self.collection = collection
        self.headers = {"Content-Type": "application/json"}
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist yet."""
        try:
            resp = requests.post(
                f"{self.base_url}/collections",
                json={"name": self.collection},
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )
            logger.info(f"Collection '{self.collection}' ready (status: {resp.status_code})")
        except requests.ConnectionError:
            logger.error(f"Can't connect to Endee at {self.base_url} — is the server running?")
        except requests.Timeout:
            logger.error("Endee connection timed out")

    def insert(self, vectors: List[List[float]], documents: List[Dict]) -> bool:
        """Insert vectors with their text and metadata into Endee."""
        payload = [
            {"vector": vec, "metadata": doc["metadata"], "text": doc["text"], "id": doc["id"]}
            for vec, doc in zip(vectors, documents)
        ]

        try:
            resp = requests.post(
                f"{self.base_url}/collections/{self.collection}/insert",
                json={"items": payload},
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 200:
                logger.info(f"Inserted {len(payload)} vectors")
                return True
            logger.error(f"Insert failed: {resp.status_code} — {resp.text}")
            return False
        except (requests.ConnectionError, requests.Timeout) as e:
            logger.error(f"Insert request failed: {e}")
            return False

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        """Search for the most similar vectors — returns top_k results."""
        try:
            resp = requests.post(
                f"{self.base_url}/collections/{self.collection}/search",
                json={"vector": query_vector, "top_k": top_k},
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 200:
                results = resp.json()
                return [
                    {"text": item.get("text", ""), "metadata": item.get("metadata", {}), "score": item.get("score", 0.0)}
                    for item in results.get("results", [])
                ]
            logger.error(f"Search failed: {resp.status_code}")
            return []
        except (requests.ConnectionError, requests.Timeout) as e:
            logger.error(f"Search request failed: {e}")
            return []
