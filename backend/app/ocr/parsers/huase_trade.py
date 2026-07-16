"""同花顺交易流水解析器（3 行排版：操作行 / 价格行 / 数量行）"""

import logging
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from ..base import OCRResult
from .base import BaseParser

logger = logging.getLogger(__name__)

ACTION_KEYWORDS = ["清仓", "卖出", "买入", "建仓"]
INFO_KEYWORDS = ["清仓后", "T盈亏", "T+3", "参考"]


class HuaseTradeParser(BaseParser):
    """同花顺（华鑫证券）交易流水解析器"""

    @staticmethod
    def _parse_decimal(text: str) -> Optional[Decimal]:
        """解析数字字符串（支持千位分隔符、正负号、百分号）"""
        cleaned = text.replace(",", "").replace(" ", "").replace(">", "")
        # 处理 "+" 号（保留正负）
        if cleaned.startswith("+") and len(cleaned) > 1:
            cleaned = cleaned[1:]
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    def _clean_text(self, text: str) -> str:
        """清理 OCR 噪音"""
        for kw in ACTION_KEYWORDS:
            if text.startswith(kw) and len(text) > len(kw):
                return kw
        return text

    def _is_action_line(self, texts: List[str]) -> Optional[str]:
        """检测是否为操作行，返回操作类型或 None"""
        for t in texts:
            cleaned = self._clean_text(t)
            if cleaned in ACTION_KEYWORDS:
                return cleaned
        return None

    def _is_label_line(self, texts: List[str], label: str) -> bool:
        """检测是否包含指定标签（如"价格""数量"）"""
        return any(label in t for t in texts)

    def _is_info_row(self, texts: List[str]) -> bool:
        """检测是否为额外信息行"""
        joined = " ".join(texts)
        return any(kw in joined for kw in INFO_KEYWORDS)

    def _is_header(self, texts: List[str]) -> bool:
        """检测是否为表头行"""
        headers = {"流水明细", "操作", "日期", "价格", "金额", "数量", "税费"}
        joined = " ".join(texts)
        return any(h in joined for h in headers)

    def _find_date(self, texts: List[str]) -> Optional[str]:
        """查找 YYYY-MM-DD 格式的日期"""
        for t in texts:
            m = re.search(r"\d{4}-\d{2}-\d{2}", t)
            if m:
                return m.group()
        return None

    def _extract_value_after_label(
        self, texts: List[str], label: str
    ) -> Optional[Decimal]:
        """提取标签后的数值"""
        for i, t in enumerate(texts):
            if label in t:
                val_str = t.replace(label, "").strip()
                if val_str:
                    d = self._parse_decimal(val_str)
                    if d is not None:
                        return d
                if i + 1 < len(texts):
                    d = self._parse_decimal(texts[i + 1])
                    if d is not None:
                        return d
        return None

    def _parse_gas(self, texts: List[str]) -> Optional[Decimal]:
        """从数量行提取 gas（税费/费用后的数值）"""
        for i, t in enumerate(texts):
            if "税费" in t or "费用" in t:
                val_str = (
                    t.replace("税费", "")
                    .replace("费用", "")
                    .replace(">", "")
                    .strip()
                )
                if val_str:
                    d = self._parse_decimal(val_str)
                    if d is not None:
                        return d
                if i + 1 < len(texts):
                    d = self._parse_decimal(
                        texts[i + 1].replace(">", "")
                    )
                    if d is not None:
                        return d
        return None

    def parse(self, ocr_results: List[OCRResult]) -> Dict[str, Any]:
        rows = self._group_by_y(ocr_results)

        transactions: List[Dict[str, Any]] = []
        i = 0
        while i < len(rows):
            texts = [
                r.text for r in sorted(rows[i], key=lambda r: r.bbox[0])
            ]

            # 跳过表头、额外信息行
            if self._is_header(texts) or self._is_info_row(texts):
                i += 1
                continue

            action = self._is_action_line(texts)
            if not action:
                i += 1
                continue

            date_val = self._find_date(texts)
            if not date_val:
                i += 1
                continue

            # 查找接下来的价格行和数量行（最多向前看 5 行）
            price_line = None
            qty_line = None
            max_skip = 0

            for j in range(1, min(len(rows) - i, 6)):
                next_texts = [
                    r.text
                    for r in sorted(
                        rows[i + j], key=lambda r: r.bbox[0]
                    )
                ]

                # 跳过 info 行，但计数它们
                if self._is_info_row(next_texts):
                    continue

                if self._is_label_line(next_texts, "价格"):
                    price_line = next_texts
                    max_skip = max(max_skip, j)
                elif self._is_label_line(next_texts, "数量"):
                    qty_line = next_texts
                    max_skip = max(max_skip, j)

                if price_line and qty_line:
                    break

            if not price_line or not qty_line:
                logger.warning(
                    "未找到价格行或数量行，跳过: %s", texts
                )
                i += 1
                continue

            price = self._extract_value_after_label(price_line, "价格")
            qty_raw = self._extract_value_after_label(qty_line, "数量")
            gas = self._parse_gas(qty_line)

            if price is None or qty_raw is None:
                logger.warning(
                    "价格或数量解析失败: price=%s, qty=%s", price, qty_raw
                )
                i += 1
                continue

            # 操作方向
            direction = 1 if action in ("买入", "建仓") else -1
            quantity = direction * abs(int(qty_raw))

            tx: Dict[str, Any] = {
                "action": "buy" if direction > 0 else "sell",
                "traded_at": date_val,
                "price": float(price),
                "quantity": quantity,
                "gas": float(gas) if gas else 0.0,
            }

            transactions.append(tx)
            i += max_skip + 1  # 跳过已处理的行

        return {
            "version": "1",
            "exported_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "transactions": transactions,
        }
