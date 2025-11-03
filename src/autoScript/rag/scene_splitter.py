"""Utilities for narrative aware scene splitting."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, Iterable, List


@dataclass
class SceneDocument:
    """Container for a single scene extracted from source material."""

    identifier: str
    text: str
    metadata: Dict[str, str]


class SceneSplitter:
    """Split long form prose into narrative aware scenes.

    The splitter uses lightweight heuristics inspired by the production
    proposal: detecting temporal markers, location changes and major
    character transitions. This keeps scene retrieval aligned with
    screenplay friendly units while avoiding destructive fixed-size chunking.
    """

    TIME_MARKERS = [
        "天后",
        "夜里",
        "清晨",
        "傍晚",
        "随后",
        "与此同时",
        "此刻",
        "第二天",
        "三天后",
    ]
    LOCATION_MARKERS = [
        "到了",
        "回到",
        "来到",
        "走进",
        r"在\s+.*?(?:里|内|外|旁)",
    ]

    def __init__(self, *, min_scene_chars: int = 300, max_scene_chars: int = 3200) -> None:
        self.min_scene_chars = min_scene_chars
        self.max_scene_chars = max_scene_chars

    def split(self, text: str, *, source: str) -> List[SceneDocument]:
        """Split the provided text into scene documents."""

        normalised = text.replace("\r\n", "\n")
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", normalised) if p.strip()]
        candidates = self._group_paragraphs(paragraphs)
        documents: List[SceneDocument] = []
        for index, block in enumerate(candidates, start=1):
            joined = "\n".join(block).strip()
            if not joined:
                continue
            doc_id = f"{source}-scene-{index:04d}"
            documents.append(
                SceneDocument(
                    identifier=doc_id,
                    text=joined,
                    metadata={"source": source, "order": str(index)},
                )
            )
        return documents

    def _group_paragraphs(self, paragraphs: Iterable[str]) -> List[List[str]]:
        """Merge neighbouring paragraphs into scene-sized groups."""

        groups: List[List[str]] = []
        buffer: List[str] = []
        for paragraph in paragraphs:
            buffer.append(paragraph)
            total_chars = sum(len(p) for p in buffer)
            if total_chars < self.min_scene_chars:
                continue
            if self._has_scene_boundary(paragraph) or total_chars >= self.max_scene_chars:
                groups.append(buffer)
                buffer = []
        if buffer:
            groups.append(buffer)
        return groups

    def _has_scene_boundary(self, paragraph: str) -> bool:
        lowered = paragraph.lower()
        time_hit = any(marker in paragraph for marker in self.TIME_MARKERS)
        location_hit = any(re.search(pattern, paragraph) for pattern in self.LOCATION_MARKERS)
        dialogue_density = lowered.count("“") + lowered.count("\"")
        return bool(time_hit or location_hit or dialogue_density >= 4)


__all__ = ["SceneSplitter", "SceneDocument"]
