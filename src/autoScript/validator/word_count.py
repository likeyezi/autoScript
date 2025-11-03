"""Word-count based validation."""
from __future__ import annotations

from .base import ValidationResult


def check_word_count(script_text: str, *, min_count: int = 1000, max_count: int = 1300) -> ValidationResult:
    """Ensure the script length is within the configured character range."""

    count = len(script_text)
    if min_count <= count <= max_count:
        return ValidationResult(True, f"WordCount OK: {count} characters")
    return ValidationResult(
        False,
        f"WordCountError: {count} characters, required between {min_count}-{max_count}",
    )


__all__ = ["check_word_count"]
