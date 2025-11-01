"""Custom tool to validate per-episode word counts."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Dict, List

from crewai_tools import BaseTool


EPISODE_HEADER_PATTERN = re.compile(r"^第(\d{1,3})集\s*$", re.MULTILINE)
SCENE_HEADER_PATTERN = re.compile(r"^\[(\d{1,3})-(\d{1,2})]\s.+$", re.MULTILINE)


@dataclass
class EpisodeCountResult:
    episode: int
    word_count: int
    scene_count: int

    def to_dict(self) -> Dict[str, int]:
        return {
            "episode": self.episode,
            "word_count": self.word_count,
            "scene_count": self.scene_count,
        }


class EpisodeWordCountTool(BaseTool):
    """Tool that checks each episode in the screenplay for word-count compliance."""

    name = "EpisodeWordCountTool"
    description = (
        "统计剧本中每一集的字数，并返回是否符合 1000-1200 字区间。"
        "如发现不合规集数，会指出需要返工的集次，并提示场景数量低于 2 的章节。"
    )

    def _run(self, screenplay: str) -> str:
        counts = self._count_words_per_episode(screenplay)
        violations: List[EpisodeCountResult] = [
            result
            for result in counts
            if result.word_count < 1000 or result.word_count > 1200
        ]
        scene_warnings = [
            result.to_dict()
            for result in counts
            if result.scene_count < 2
        ]
        payload = {
            "episodes": [result.to_dict() for result in counts],
            "violations": [result.to_dict() for result in violations],
            "scene_warnings": scene_warnings,
            "status": "pass" if not violations else "fail",
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    async def _arun(self, screenplay: str) -> str:
        return self._run(screenplay)

    @staticmethod
    def _count_words_per_episode(screenplay: str) -> List[EpisodeCountResult]:
        matches = list(EPISODE_HEADER_PATTERN.finditer(screenplay))
        if not matches:
            return [
                EpisodeCountResult(
                    episode=1,
                    word_count=_word_count(screenplay),
                    scene_count=len(SCENE_HEADER_PATTERN.findall(screenplay)),
                )
            ]

        results: List[EpisodeCountResult] = []
        for index, match in enumerate(matches):
            episode_number = int(match.group(1))
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(screenplay)
            episode_content = screenplay[start:end]
            scene_count = len(SCENE_HEADER_PATTERN.findall(episode_content))
            word_count = _word_count(episode_content)
            results.append(
                EpisodeCountResult(
                    episode=episode_number,
                    word_count=word_count,
                    scene_count=scene_count,
                )
            )
        return results


def _word_count(text: str) -> int:
    """Approximate word count by splitting on whitespace and punctuation."""
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", text)
    return len(tokens)


__all__ = ["EpisodeWordCountTool"]
