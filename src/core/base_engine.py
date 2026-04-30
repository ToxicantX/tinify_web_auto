from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Callable, Optional


@dataclass
class CompressResult:
    original_path: str
    original_name: str
    original_size: int
    compressed_size: int
    output_path: str
    duration_ms: int
    success: bool
    error: Optional[str] = None

    @property
    def ratio(self) -> float:
        if self.original_size > 0:
            return round((1 - self.compressed_size / self.original_size) * 100, 1)
        return 0.0


class BaseEngine(ABC):

    @abstractmethod
    def validate(self) -> tuple[bool, str]:
        """Validate engine prerequisites (e.g. API key, browser). Returns (ok, message)."""
        ...

    @abstractmethod
    def compress(self, input_path: str, output_path: str) -> CompressResult:
        ...

    @abstractmethod
    def compress_batch(self, files: list[str], output_dir: str,
                       progress_callback: Optional[Callable] = None) -> list[CompressResult]:
        ...
