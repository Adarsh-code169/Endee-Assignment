import logging
import requests
import json
import msgpack
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
                f"{self.base_url}/api/v1/index/create",
                json={"index_name": self.collection, "dim": 384, "space_type": "cosine"},
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )
            if resp.status_code in (200, 409):
                logger.info(f"Collection '{self.collection}' ready (status: {resp.status_code})")
            else:
                logger.error(f"Failed to create collection: {resp.status_code} — {resp.text}")
        except requests.ConnectionError:
            logger.error(f"Can't connect to Endee at {self.base_url} — is the server running?")
        except requests.Timeout:
            logger.error("Endee connection timed out")

    def insert(self, vectors: List[List[float]], documents: List[Dict]) -> bool:
        """Insert vectors with their text and metadata into Endee."""
        payload = [
            {"vector": vec, "meta": json.dumps({"text": doc["text"], **doc["metadata"]}), "filter": "", "id": doc["id"]}
            for vec, doc in zip(vectors, documents)
        ]

        try:
            resp = requests.post(
                f"{self.base_url}/api/v1/index/{self.collection}/vector/insert",
                json=payload,
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
                f"{self.base_url}/api/v1/index/{self.collection}/search",
                json={"vector": query_vector, "k": top_k},
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 200:
                results = msgpack.unpackb(resp.content, raw=False)
                parsed = []
                # Result format is usually: [distance, id, meta_string, filter, ...]
                for item in results:
                    if len(item) < 3:
                        continue
                    
                    dist, doc_id, meta_bytes = item[0], item[1], item[2]
                    
                    meta_str = meta_bytes if isinstance(meta_bytes, str) else meta_bytes.decode('utf-8', errors='ignore')
                    try:
                        meta_dict = json.loads(meta_str) if meta_str else {}
                    except json.JSONDecodeError:
                        meta_dict = {}

                    text = meta_dict.pop("text", "")
                    score = 1.0 - float(dist)

                    parsed.append({
                        "text": text,
                        "metadata": meta_dict,
                        "score": score
                    })

                return parsed
            logger.error(f"Search failed: {resp.status_code} — {resp.text}")
            return []
        except (requests.ConnectionError, requests.Timeout) as e:
            logger.error(f"Search request failed: {e}")
            return []

