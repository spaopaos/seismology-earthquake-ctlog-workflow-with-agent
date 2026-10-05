# -*- coding: utf-8 -*-
import functools
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class CommandResult:
    """Unified result returned by every command, consumed by both CLI and frontend."""
    success: bool
    message: str
    data: Any = None
    errors: list[str] = field(default_factory=list)
    output_files: list[Path] = field(default_factory=list)


class BaseCommand:
    """
    All commands inherit from this.
    - CLI calls .run() directly, captures CommandResult
    - Frontend calls .run() in a thread, updates widgets via callbacks
    """

    def __init__(self, progress_callback: Optional[Callable[[str, int], None]] = None):
        # progress_callback(message, percent) — Panel widgets or tqdm use this
        self.progress_callback = progress_callback or self._default_progress

    def _default_progress(self, message: str, percent: int):
        """CLI fallback: just log."""
        logger.info(f"[{percent:3d}%] {message}")

    def progress(self, message: str, percent: int):
        self.progress_callback(message, percent)

    def run(self) -> CommandResult:
        raise NotImplementedError


def safe_command(fn: Callable[..., CommandResult]) -> Callable[..., CommandResult]:
    """Decorator for Command.run() methods: converts any raised exception into
    a failed CommandResult(success=False, message=str(e), errors=[str(e)])
    instead of every subclass repeating the same try/except."""

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs) -> CommandResult:
        try:
            return fn(self, *args, **kwargs)
        except Exception as e:
            return CommandResult(success=False, message=str(e), errors=[str(e)])

    return wrapper