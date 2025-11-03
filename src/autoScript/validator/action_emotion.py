"""Emotion detection for action-only lines."""
from __future__ import annotations

import re
from typing import Iterable

from .base import ValidationResult

EMOTION_KEYWORDS: Iterable[str] = (
    "愤怒",
    "生气",
    "悲伤",
    "绝望",
    "喜极",
    "兴奋",
    "害怕",
    "恐惧",
    "焦虑",
    "无奈",
    "紧张",
    "惊呆",
)

ACTION_REGEX = re.compile(r"^\s*△\s*.+?：(.*)$")


class EmotionDetector:
    """Best-effort detector with optional transformer pipeline support."""

    def __init__(self, model: str | None = None) -> None:
        self._pipeline = None
        if model:
            self._initialise_pipeline(model)
        else:
            try:
                from transformers import pipeline  # type: ignore

                self._pipeline = pipeline("text-classification", model="uer/roberta-base-finetuned-jd-binary-chinese")
            except Exception:
                self._pipeline = None

    def _initialise_pipeline(self, model: str) -> None:
        try:
            from transformers import pipeline  # type: ignore

            self._pipeline = pipeline("text-classification", model=model)
        except Exception:
            self._pipeline = None

    def detect(self, text: str) -> str:
        if self._pipeline is not None:
            result = self._pipeline(text, truncation=True)[0]
            label = result.get("label", "neutral")
            return label.lower()
        lowered = text.lower()
        return "neutral" if not any(keyword in lowered for keyword in EMOTION_KEYWORDS) else "emotional"


_default_detector = EmotionDetector()


def check_action_lines(script_text: str, *, detector: EmotionDetector | None = None) -> ValidationResult:
    """Ensure △ lines only contain physical actions."""

    detector = detector or _default_detector
    errors: list[str] = []
    for index, line in enumerate(script_text.splitlines(), start=1):
        match = ACTION_REGEX.match(line)
        if not match:
            continue
        description = match.group(1).strip()
        if not description:
            continue
        emotion = detector.detect(description)
        if emotion != "neutral":
            errors.append(
                f"Line {index}: ActionLineError -> '{description}' flagged as {emotion}"
            )
    if not errors:
        return ValidationResult(True, "Action Lines OK")
    return ValidationResult(False, "\n".join(errors))


__all__ = ["check_action_lines", "EmotionDetector"]
