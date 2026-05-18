import hashlib
import math

import httpx

from app.core.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._local_model = None

    async def embed(self, text: str) -> list[float]:
        provider = self.settings.embeddings_provider
        if provider == "openai" and self.settings.openai_api_key:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                    json={"model": "text-embedding-3-small", "input": text},
                )
                response.raise_for_status()
                return response.json()["data"][0]["embedding"]
        if provider == "local":
            from sentence_transformers import SentenceTransformer

            if self._local_model is None:
                self._local_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            return self._local_model.encode(text).tolist()
        return self._hash_embedding(text)

    async def semantic_matrix(self, texts: list[str]) -> dict:
        vectors = [await self.embed(text) for text in texts]
        matrix = [[round(self._cosine(left, right), 4) for right in vectors] for left in vectors]
        pairs = [matrix[i][j] for i in range(len(matrix)) for j in range(i + 1, len(matrix))]
        avg = sum(pairs) / len(pairs) if pairs else 1.0
        return {"matrix": matrix, "average_pairwise_similarity": round(avg, 4)}

    def _hash_embedding(self, text: str, dims: int = 128) -> list[float]:
        vector = [0.0] * dims
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:2], "big") % dims
            sign = 1 if digest[2] % 2 == 0 else -1
            vector[idx] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def _cosine(self, left: list[float], right: list[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left)) or 1.0
        right_norm = math.sqrt(sum(value * value for value in right)) or 1.0
        return dot / (left_norm * right_norm)
