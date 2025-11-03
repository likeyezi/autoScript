"""Formatting validation rules for screenplay layout."""
from __future__ import annotations

import re
from typing import Iterable, List

from .base import ValidationResult


SCENE_REGEX = re.compile(r"^\s*\[\d+-\d+\]\s+.+?\s*-\s*(?:内|外)\s*-\s*(?:日|夜)\s*$")
ACTION_REGEX = re.compile(r"^\s*△\s*.+?：.+$")
NARRATION_REGEX = re.compile(r"^\s*旁白：.+$")
OS_REGEX = re.compile(r"^\s*OS：.+$")
DIALOGUE_REGEX = re.compile(r"^\s*[\u4e00-\u9fffA-Za-z0-9_]+：.*$")
EMPTY_REGEX = re.compile(r"^\s*$")

ALLOWED_PATTERNS: Iterable[re.Pattern[str]] = (
    SCENE_REGEX,
    ACTION_REGEX,
    NARRATION_REGEX,
    OS_REGEX,
    DIALOGUE_REGEX,
    EMPTY_REGEX,
)


def check_format(script_text: str) -> ValidationResult:
    """Ensure every line matches one of the whitelisted screenplay patterns."""

    errors: List[str] = []
    for index, line in enumerate(script_text.splitlines(), start=1):
        if any(pattern.match(line) for pattern in ALLOWED_PATTERNS):
            continue
        errors.append(f"Line {index}: FormatError -> {line.strip()}")
    if not errors:
        return ValidationResult(True, "Format OK")
    return ValidationResult(False, "\n".join(errors))


__all__ = ["check_format"]
