"""RapidOCR ONNX Runtime 引擎 — 无 PaddlePaddle 依赖"""

import logging
from typing import List

from .base import BaseOCREngine, OCRResult

logger = logging.getLogger(__name__)


class RapidOCREngine(BaseOCREngine):
    """基于 rapidocr_onnxruntime 的 OCR 引擎"""

    def __init__(self):
        self._ocr = None

    def _ensure_loaded(self):
        if self._ocr is not None:
            return
        try:
            from rapidocr_onnxruntime import RapidOCR

            self._ocr = RapidOCR()
            logger.info("RapidOCR 模型加载完成")
        except ImportError:
            raise RuntimeError(
                "RapidOCR 未安装。请运行: pip install rapidocr_onnxruntime\n"
                "或使用 --engine qwen 切换到 Qwen-VL API 引擎"
            )
        except Exception as e:
            raise RuntimeError(f"RapidOCR 初始化失败: {e}")

    @staticmethod
    def _poly_to_bbox(poly) -> List[float]:
        """将多边形 [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] 转为 [x1,y1,x2,y2]"""
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        return [min(xs), min(ys), max(xs), max(ys)]

    def recognize(self, image_path: str) -> List[OCRResult]:
        self._ensure_loaded()

        result, _ = self._ocr(image_path)
        if not result:
            logger.warning(f"RapidOCR 未在截图 {image_path} 中检测到任何文字")
            return []

        ocr_results: List[OCRResult] = []
        for bbox, text, confidence in result:
            if not text or not text.strip():
                continue
            ocr_results.append(
                OCRResult(
                    text=text.strip(),
                    bbox=self._poly_to_bbox(bbox),
                    confidence=confidence,
                )
            )

        logger.info(
            "RapidOCR 完成识别 %s: %d 个文本框", image_path, len(ocr_results)
        )
        return ocr_results
