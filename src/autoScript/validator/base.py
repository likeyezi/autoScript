"""Common types for validator tooling."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Protocol


@dataclass
class ValidationResult:
    """Result returned by each deterministic validation tool."""

    passed: bool
    message: str


class ValidationTool(Protocol):
    """Protocol describing a validation callable."""

    def __call__(self, script_text: str) -> ValidationResult:
        ...


ValidationPipeline = Callable[[str], List[str]]

__all__ = ["ValidationResult", "ValidationTool", "ValidationPipeline"]
