"""Punctuation validation rules."""
from __future__ import annotations

from .base import ValidationResult


FORBIDDEN_PUNCT = {"...", "…", "——", "—", "--"}


def check_punctuation(script_text: str) -> ValidationResult:
    """Fail if the script contains forbidden punctuation marks."""

    offending = sorted({mark for mark in FORBIDDEN_PUNCT if mark in script_text})
    if not offending:
        return ValidationResult(True, "Punctuation OK")
    return ValidationResult(
        False,
        "PunctuationError: Forbidden punctuation found -> " + ", ".join(offending),
    )


__all__ = ["check_punctuation", "FORBIDDEN_PUNCT"]
