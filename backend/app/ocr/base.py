from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class OCRResult:
    text: str
    bbox: List[float]
    confidence: float = 1.0
    line_group: int = 0


class BaseOCREngine(ABC):
    @abstractmethod
    def recognize(self, image_path: str) -> List[OCRResult]:
        ...
