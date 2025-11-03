"""Dual retrieval augmented generation utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .scene_splitter import SceneDocument


@dataclass
class RetrievalResult:
    """Represents a single retrieved scene sample."""

    score: float
    text: str
    metadata: Dict[str, str]


class DualRAGIndex:
    """Manages parallel content/style retrieval stores."""

    def __init__(self, *, max_features: int = 8192) -> None:
        self._content_vectorizer = TfidfVectorizer(max_features=max_features)
        self._style_vectorizer = TfidfVectorizer(max_features=max_features)
        self._content_documents: List[SceneDocument] = []
        self._style_documents: List[SceneDocument] = []
        self._content_matrix = None
        self._style_matrix = None

    @property
    def content_documents(self) -> Sequence[SceneDocument]:
        return tuple(self._content_documents)

    @property
    def style_documents(self) -> Sequence[SceneDocument]:
        return tuple(self._style_documents)

    def index_content(self, documents: Iterable[SceneDocument]) -> None:
        self._content_documents = list(documents)
        corpus = [doc.text for doc in self._content_documents]
        if corpus:
            self._content_matrix = self._content_vectorizer.fit_transform(corpus)
        else:
            self._content_matrix = None

    def index_style(self, documents: Iterable[SceneDocument]) -> None:
        self._style_documents = list(documents)
        corpus = [doc.text for doc in self._style_documents]
        if corpus:
            self._style_matrix = self._style_vectorizer.fit_transform(corpus)
        else:
            self._style_matrix = None

    def retrieve_content(self, query: str, *, top_k: int = 3) -> List[RetrievalResult]:
        return self._retrieve(
            query,
            top_k=top_k,
            matrix=self._content_matrix,
            vectorizer=self._content_vectorizer,
            documents=self._content_documents,
        )

    def retrieve_style(self, query: str, *, top_k: int = 3) -> List[RetrievalResult]:
        return self._retrieve(
            query,
            top_k=top_k,
            matrix=self._style_matrix,
            vectorizer=self._style_vectorizer,
            documents=self._style_documents,
        )

    def _retrieve(
        self,
        query: str,
        *,
        top_k: int,
        matrix,
        vectorizer: TfidfVectorizer,
        documents: Sequence[SceneDocument],
    ) -> List[RetrievalResult]:
        if not query.strip() or matrix is None or not documents:
            return []
        query_vector = vectorizer.transform([query])
        similarity = cosine_similarity(query_vector, matrix)[0]
        if not len(similarity):
            return []
        top_indices = np.argsort(similarity)[::-1][:top_k]
        results: List[RetrievalResult] = []
        for index in top_indices:
            score = float(similarity[index])
            doc = documents[int(index)]
            results.append(RetrievalResult(score=score, text=doc.text, metadata=doc.metadata))
        return results


__all__ = ["DualRAGIndex", "RetrievalResult"]
