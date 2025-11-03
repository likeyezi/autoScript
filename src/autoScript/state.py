"""State definitions for the LangGraph based novel-to-script workflow."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, TypedDict

from typing_extensions import NotRequired


@dataclass
class EpisodeTask:
    """Represents a single episode level writing assignment."""

    episode_number: int
    title: str
    synopsis: str
    rag_content_query: str
    rag_style_query: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_number": self.episode_number,
            "title": self.title,
            "synopsis": self.synopsis,
            "rag_content_query": self.rag_content_query,
            "rag_style_query": self.rag_style_query,
        }


class NovelAdaptationState(TypedDict, total=False):
    """Shared LangGraph state passed between all nodes."""

    human_blueprint: Dict[str, Any]
    episode_tasks: List[Dict[str, Any]]
    current_task: Dict[str, Any]
    episode_index: int
    content_chunks: str
    style_chunks: str
    draft_script: str
    validation_errors: List[str]
    feedback: str
    retry_count: int
    delivered_scripts: List[str]
    requires_human_review: bool
    metadata: NotRequired[Dict[str, Any]]


DEFAULT_STATE: NovelAdaptationState = {
    "episode_tasks": [],
    "delivered_scripts": [],
    "retry_count": 0,
    "episode_index": 0,
}


__all__ = ["EpisodeTask", "NovelAdaptationState", "DEFAULT_STATE"]
