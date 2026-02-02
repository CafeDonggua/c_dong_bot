from __future__ import annotations

from typing import List

from openai import OpenAI


class EmbeddingClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    def embed(self, text: str) -> List[float]:
        response = self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return list(response.data[0].embedding)
