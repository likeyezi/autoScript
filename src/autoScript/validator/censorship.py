"""Content safety validation."""
from __future__ import annotations

from typing import Iterable

from .base import ValidationResult

SENSITIVE_KEYWORDS: Iterable[str] = (
    "黄赌毒",
    "赌博",
    "毒品",
    "贩毒",
    "嫖娼",
    "吸毒",
)


def check_censorship(script_text: str) -> ValidationResult:
    """Detect obvious content policy violations using a keyword deny-list."""

    lowered = script_text.lower()
    hits = [keyword for keyword in SENSITIVE_KEYWORDS if keyword.lower() in lowered]
    if not hits:
        return ValidationResult(True, "Censorship OK")
    return ValidationResult(False, "CensorshipError: forbidden topics -> " + ", ".join(hits))


__all__ = ["check_censorship", "SENSITIVE_KEYWORDS"]
