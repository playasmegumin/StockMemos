import json
import logging
from typing import List

from .base import BaseOCREngine, OCRResult

logger = logging.getLogger(__name__)


class PaddleOCREngine(BaseOCREngine):
    def __init__(self, use_gpu: bool = False):
        self._use_gpu = use_gpu
        self._ocr = None

    def _ensure_loaded(self):
        if self._ocr is not None:
            return
        try:
            from paddleocr import PaddleOCR

            # PaddleOCR 3.x: 仅传 lang 参数
            # 需在外层设置环境变量 FLAGS_use_pir_api=0 避免 PIR 兼容问题
            self._ocr = PaddleOCR(lang="ch")
            logger.info("PaddleOCR 模型加载完成")
        except ImportError:
            raise RuntimeError(
                "PaddleOCR 未安装。请运行: pip install paddleocr paddlepaddle\n"
                "或使用 --engine qwen 切换到 Qwen-VL API 引擎"
            )
        except Exception as e:
            raise RuntimeError(f"PaddleOCR 初始化失败: {e}")

    def _parse_poly(self, poly) -> list:
        """将多边形坐标转为 bbox [x1,y1,x2,y2]，兼容列表和元组"""
        if not poly:
            return [0, 0, 0, 0]
        xs = [poly[i] for i in range(0, len(poly), 2)]
        ys = [poly[i + 1] for i in range(0, len(poly), 2)]
        return [min(xs), min(ys), max(xs), max(ys)]

    def recognize(self, image_path: str) -> List[OCRResult]:
        self._ensure_loaded()

        raw = self._ocr.ocr(image_path)

        if not raw or not raw[0]:
            logger.warning(f"PaddleOCR 未在截图 {image_path} 中检测到任何文字")
            return []

        results: List[OCRResult] = []
        for item in raw[0]:
            poly = item[0]
            text, confidence = item[1]
            bbox = self._parse_poly(poly)
            results.append(OCRResult(text=text, bbox=bbox, confidence=confidence))

        logger.info(
            "PaddleOCR 完成识别 %s: %d 个文本框", image_path, len(results)
        )
        return results
