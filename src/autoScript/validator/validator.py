"""Deterministic screenplay validator orchestrating all tools."""
from __future__ import annotations

from typing import Iterable, List

from .action_emotion import check_action_lines
from .base import ValidationResult, ValidationTool
from .censorship import check_censorship
from .formatting import check_format
from .punctuation import check_punctuation
from .word_count import check_word_count


DEFAULT_VALIDATORS: Iterable[ValidationTool] = (
    check_word_count,
    check_punctuation,
    check_format,
    check_action_lines,
    check_censorship,
)


def validate_script(script_text: str, *, validators: Iterable[ValidationTool] | None = None) -> List[str]:
    """Run all validators and collect failure messages."""

    validators = tuple(validators or DEFAULT_VALIDATORS)
    errors: List[str] = []
    for validator in validators:
        result: ValidationResult = validator(script_text)
        if not result.passed:
            errors.append(result.message)
    return errors


__all__ = ["validate_script", "DEFAULT_VALIDATORS"]
