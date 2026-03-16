from __future__ import annotations

import hashlib
import asyncio
import numpy as np
import structlog
import google.generativeai as genai
from backend.config import settings

logger = structlog.get_logger()


class EmbeddingClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._cache: dict[str, list[float]] = {}
        self._dim = settings.EMBEDDING_DIMENSION

    async def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        results = []
        for text in texts:
            key = self._hash(text)
            if key in self._cache:
                results.append(self._cache[key])
            else:
                try:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda t=text: genai.embed_content(
                            model=settings.EMBEDDING_MODEL,
                            content=t,
                            task_type="retrieval_document"
                        )
                    )
                    vec = result['embedding']
                    self._cache[key] = vec
                    results.append(vec)
                except Exception as e:
                    logger.warning("embedding_failed", error=str(e))
                    results.append([0.0] * self._dim)
        return np.array(results, dtype=np.float32)

    async def embed_single(self, text: str) -> np.ndarray:
        matrix = await self.embed([text])
        return matrix[0]

    async def embed_texts(self, texts: list[str]) -> np.ndarray:
        return await self.embed(texts)

    async def embed_query(self, text: str) -> np.ndarray:
        return await self.embed_single(text)

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]