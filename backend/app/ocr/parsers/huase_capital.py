"""同花顺银证转账解析器（队列匹配：按行提取、按序配对）"""

import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from ..base import OCRResult
from .base import BaseParser

logger = logging.getLogger(__name__)

MONTH_GROUP_RE = re.compile(r"(\d{4})-(\d{2})")
TIME_RE = re.compile(r"(\d{2})-(\d{2})\s*(\d{2}:\d{2})?")
AMOUNT_RE = re.compile(r"[+-]\s*[\d,]+\.\d{2}")
OP_MAP: Dict[str, str] = {
    "现金存入": "deposit",
    "银证转入": "deposit",
    "银行存款": "deposit",
    "银证转出": "withdraw",
    "银行取款": "withdraw",
}
HEADER_YEAR_RE = re.compile(r"(\d{4})/\d{2}/\d{2}")
HEADER_KEYWORDS = {
    "银证转账", "操作/时间", "净转入", "近1年", "平安证券", "11:33",
}
SKIP_PATTERNS = [re.compile(p) for p in [
    r"清仓后", r"T盈亏", r"T\+3",
]]


class HuaseCapitalParser(BaseParser):
    """同花顺银证转账解析器

    每笔记录字段分布在不同行中。策略：按行扫描提取字段，
    维护待匹配队列，字段累积足够后配对发射。
    """

    def __init__(self):
        self._page_year: Optional[int] = None

    @staticmethod
    def _parse_decimal(text: str) -> Optional[Decimal]:
        cleaned = text.replace(",", "").replace(" ", "").replace("+", "")
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    def _extract_page_year(self, rows):
        for row in rows:
            joined = " ".join(r.text for r in row)
            m = HEADER_YEAR_RE.search(joined)
            if m:
                self._page_year = int(m.group(1))
                return

    def _is_header(self, texts: List[str]) -> bool:
        joined = " ".join(texts)
        return any(h in joined for h in HEADER_KEYWORDS)

    def _is_skip_row(self, texts: List[str]) -> bool:
        joined = " ".join(texts)
        return any(p.search(joined) for p in SKIP_PATTERNS)

    def _find_op(self, text: str) -> Optional[str]:
        for op in OP_MAP:
            if op in text:
                return op
        return None

    def _find_amount(self, texts: List[str]) -> Optional[Decimal]:
        for t in reversed(texts):
            if AMOUNT_RE.search(t):
                return self._parse_decimal(t)
        return None

    def _find_date(self, texts: List[str]) -> Optional[str]:
        for t in texts:
            m = TIME_RE.search(t)
            if m:
                return m.group()
        return None

    def _build_flow(
        self, date_text: str, op_type: str, amount: Decimal,
        year: Optional[int],
    ) -> Optional[Dict[str, Any]]:
        m = TIME_RE.search(date_text)
        if not m:
            return None
        mm_dd = f"{m.group(1)}-{m.group(2)}"
        hh_mm = m.group(3) or "00:00"
        y = year or self._page_year or datetime.now().year
        return {
            "type": OP_MAP.get(op_type, "deposit"),
            "amount": float(amount),
            "currency": "CNY",
            "created_at": f"{y}-{mm_dd}T{hh_mm}:00",
        }

    def _try_pair(self, dates, ops, amounts, current_year):
        """从队列中取最早的 date + op + amount 配对发射"""
        while dates and ops and amounts:
            # 所有字段按 Y 排序，配对最早的三元组
            d = dates.pop(0)
            o = ops.pop(0)
            a = amounts.pop(0)
            flow = self._build_flow(d[0], o[0], a[0], current_year)
            if flow:
                return flow
        return None

    def parse(self, ocr_results: List[OCRResult]) -> Dict[str, Any]:
        rows = self._group_by_y(ocr_results)
        self._extract_page_year(rows)

        current_year: Optional[int] = None
        flows: List[Dict[str, Any]] = []

        # 三个独立队列：每个元素为 (value, y)
        date_queue: List[tuple] = []
        op_queue: List[tuple] = []
        amt_queue: List[tuple] = []

        for row in rows:
            texts = [r.text for r in sorted(row, key=lambda r: r.bbox[0])]
            joined = " ".join(texts)
            y = int(row[0].bbox[1])

            if self._is_header(texts):
                continue
            if self._is_skip_row(texts):
                continue

            m = MONTH_GROUP_RE.search(joined)
            if m and "净转入" in joined:
                current_year = int(m.group(1))
                continue

            date_str = self._find_date(texts)
            op = self._find_op(joined)
            amount = self._find_amount(texts)

            if date_str:
                date_queue.append((date_str, y))
            if op:
                op_queue.append((op, y))
            if amount is not None:
                amt_queue.append((amount, y))

            # 当三个队列都有值时，尝试发射最早一组
            flow = self._try_pair(date_queue, op_queue, amt_queue, current_year)
            if flow:
                flows.append(flow)

        # 不断尝试直到队列清空
        while True:
            flow = self._try_pair(date_queue, op_queue, amt_queue, current_year)
            if flow:
                flows.append(flow)
            else:
                break

        return {
            "version": "1",
            "exported_at": datetime.now().isoformat() + "Z",
            "capital_flows": flows,
        }
