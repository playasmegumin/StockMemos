from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..base import OCRResult


class BaseParser(ABC):
    @abstractmethod
    def parse(self, ocr_results: List[OCRResult]) -> Dict[str, Any]:
        ...

    @staticmethod
    def _group_by_y(
        results: List[OCRResult], tolerance: float = 25
    ) -> List[List[OCRResult]]:
        if not results:
            return []

        sorted_items = sorted(
            results, key=lambda r: (r.bbox[1], r.bbox[0])
        )

        rows: List[List[OCRResult]] = []
        current_row: List[OCRResult] = [sorted_items[0]]
        current_y = sorted_items[0].bbox[1]

        for item in sorted_items[1:]:
            if abs(item.bbox[1] - current_y) <= tolerance:
                current_row.append(item)
            else:
                rows.append(sorted(current_row, key=lambda r: r.bbox[0]))
                current_row = [item]
                current_y = item.bbox[1]

        rows.append(sorted(current_row, key=lambda r: r.bbox[0]))
        return rows
