"""Tests for OCR parser logic using mock OCR results."""

from decimal import Decimal
from app.ocr.base import OCRResult
from app.ocr.parsers.huase_trade import HuaseTradeParser
from app.ocr.parsers.huase_capital import HuaseCapitalParser


def _make_ocr(text: str, y: float, x: float = 0) -> OCRResult:
    return OCRResult(text=text, bbox=[x, y, x + len(text) * 10, y + 20])


# ═══════════════════════════════════════════════
# 交易流水解析器（3行排版）
# ═══════════════════════════════════════════════

class TestHuaseTradeParser:
    """Mock 数据模拟实际截图 3-line 排版:
    Line 1 (行动作): action + date
    Line 2 (价格行): "价格" + price + "金额" + amount
    Line 3 (数量行): "数量" + qty + "费用/税费" + gas
    """

    def test_parse_single_buy(self):
        results = [
            # Action line (y=100)
            _make_ocr("建仓", 100, 20),
            _make_ocr("2025-12-19", 100, 120),
            # Price line (y=160)
            _make_ocr("价格", 160, 20),
            _make_ocr("58.440", 160, 120),
            _make_ocr("金额", 160, 240),
            _make_ocr("5,844.00", 160, 340),
            # Quantity line (y=220)
            _make_ocr("数量", 220, 20),
            _make_ocr("100", 220, 120),
            _make_ocr("费用", 220, 240),
            _make_ocr("5.06", 220, 340),
        ]

        parser = HuaseTradeParser()
        data = parser.parse(results)

        txs = data["transactions"]
        assert len(txs) == 1
        tx = txs[0]
        assert tx["action"] == "buy"
        assert tx["traded_at"] == "2025-12-19"
        assert tx["price"] == 58.44
        assert tx["quantity"] == 100
        assert tx["gas"] == 5.06

    def test_parse_single_sell(self):
        results = [
            # Action line
            _make_ocr("清仓", 100, 20),
            _make_ocr("2026-01-08", 100, 120),
            _make_ocr("+1,513.15", 100, 400),  # PnL (ignored)
            # Price line
            _make_ocr("价格", 160, 20),
            _make_ocr("103.160", 160, 120),
            _make_ocr("金额", 160, 240),
            _make_ocr("10,316.00", 160, 340),
            # Quantity line
            _make_ocr("数量", 220, 20),
            _make_ocr("-100", 220, 120),
            _make_ocr("税费", 220, 240),
            _make_ocr("10.26", 220, 340),
        ]

        parser = HuaseTradeParser()
        data = parser.parse(results)

        txs = data["transactions"]
        assert len(txs) == 1
        tx = txs[0]
        assert tx["action"] == "sell"
        assert tx["traded_at"] == "2026-01-08"
        assert tx["price"] == 103.160
        assert tx["quantity"] == -100
        assert tx["gas"] == 10.26

    def test_parse_multiple_transactions(self):
        results = [
            # --- Record 1: buy (y=100-220) ---
            _make_ocr("建仓", 100, 20),
            _make_ocr("2025-12-19", 100, 120),
            _make_ocr("价格", 160, 20),
            _make_ocr("58.440", 160, 120),
            _make_ocr("金额", 160, 240),
            _make_ocr("5,844.00", 160, 340),
            _make_ocr("数量", 220, 20),
            _make_ocr("100", 220, 120),
            _make_ocr("费用", 220, 240),
            _make_ocr("5.06", 220, 340),
            # --- Record 2: buy (y=340-460) ---
            _make_ocr("买入", 340, 20),
            _make_ocr("2025-12-29", 340, 120),
            _make_ocr("价格", 400, 20),
            _make_ocr("84.400", 400, 120),
            _make_ocr("金额", 400, 240),
            _make_ocr("8,440.00", 400, 340),
            _make_ocr("数量", 460, 20),
            _make_ocr("100", 460, 120),
            _make_ocr("费用", 460, 240),
            _make_ocr("5.08", 460, 340),
        ]

        parser = HuaseTradeParser()
        data = parser.parse(results)

        txs = data["transactions"]
        assert len(txs) == 2
        assert txs[0]["traded_at"] == "2025-12-19"
        assert txs[0]["price"] == 58.44
        assert txs[0]["quantity"] == 100
        assert txs[1]["traded_at"] == "2025-12-29"
        assert txs[1]["quantity"] == 100

    def test_parse_trade_with_info_row(self):
        """清仓后可能有说明行，解析器需跳过"""
        results = [
            # --- Record 1: sell ---
            _make_ocr("清仓", 100, 20),
            _make_ocr("2026-01-08", 100, 120),
            _make_ocr("价格", 160, 20),
            _make_ocr("103.160", 160, 120),
            _make_ocr("金额", 160, 240),
            _make_ocr("10,316.00", 160, 340),
            _make_ocr("数量", 220, 20),
            _make_ocr("-100", 220, 120),
            _make_ocr("税费", 220, 240),
            _make_ocr("10.26", 220, 340),
            # --- Info row (skip) ---
            _make_ocr("清仓后至第3日（T+3）收盘，股价上涨26.47%", 280, 20),
            # --- Record 2: buy ---
            _make_ocr("买入", 340, 20),
            _make_ocr("2025-12-30", 340, 120),
            _make_ocr("价格", 400, 20),
            _make_ocr("87.900", 400, 120),
            _make_ocr("金额", 400, 240),
            _make_ocr("17,580.00", 400, 340),
            _make_ocr("数量", 460, 20),
            _make_ocr("200", 460, 120),
            _make_ocr("费用", 460, 240),
            _make_ocr("5.18", 460, 340),
        ]

        parser = HuaseTradeParser()
        data = parser.parse(results)

        txs = data["transactions"]
        assert len(txs) == 2
        assert txs[0]["quantity"] == -100
        assert txs[1]["quantity"] == 200

    def test_version_field(self):
        parser = HuaseTradeParser()
        data = parser.parse([])
        assert data["version"] == "1"
        assert "exported_at" in data
        assert data["transactions"] == []


# ═══════════════════════════════════════════════
# 银证转账解析器（队列匹配）
# ═══════════════════════════════════════════════

class TestHuaseCapitalParser:
    """Mock 数据模拟同花顺银证转账三字段（date/op/amount）各行分布"""

    def test_parse_single_deposit(self):
        results = [
            _make_ocr("▲ 2025-12 净转入 +500.00", 30, 20),  # month group
            _make_ocr("12-12 15:00", 100, 20),
            _make_ocr("现金存入", 100, 200),
            _make_ocr("+500.00", 100, 400),
        ]

        parser = HuaseCapitalParser()
        data = parser.parse(results)

        flows = data["capital_flows"]
        assert len(flows) == 1
        f = flows[0]
        assert f["type"] == "deposit"
        assert f["amount"] == 500.0
        assert f["currency"] == "CNY"
        assert "2025-12-12" in f["created_at"]

    def test_parse_withdraw(self):
        results = [
            _make_ocr("▲ 2025-10 净转入 +1121.00", 30, 20),
            _make_ocr("10-28 15:00", 100, 20),
            _make_ocr("银证转出", 100, 200),
            _make_ocr("-2,500.00", 100, 400),
        ]

        parser = HuaseCapitalParser()
        data = parser.parse(results)

        flows = data["capital_flows"]
        assert len(flows) == 1
        f = flows[0]
        assert f["type"] == "withdraw"
        assert f["amount"] == -2500.0
        assert "2025-10-28" in f["created_at"]

    def test_year_from_month_group(self):
        """年份从月份分组行提取"""
        results = [
            _make_ocr("▲ 2025-11 净转入 +4310.00", 30, 20),
            _make_ocr("11-05 15:00", 100, 20),
            _make_ocr("银证转入", 100, 200),
            _make_ocr("+10.00", 100, 400),
        ]

        parser = HuaseCapitalParser()
        data = parser.parse(results)

        flows = data["capital_flows"]
        assert len(flows) == 1
        assert "2025-11-05" in flows[0]["created_at"]

    def test_multiple_flows_with_different_years(self):
        """跨年月分组行正确切换年份"""
        results = [
            # 2025-11
            _make_ocr("▲ 2025-11 净转入 +4310.00", 30, 20),
            _make_ocr("11-05 15:00", 100, 20),
            _make_ocr("银证转入", 100, 200),
            _make_ocr("+10.00", 100, 400),
            # 2025-10
            _make_ocr("▲ 2025-10 净转入 +1121.00", 260, 20),
            _make_ocr("10-28 15:00", 330, 20),
            _make_ocr("银证转入", 330, 200),
            _make_ocr("+1620.00", 330, 400),
        ]

        parser = HuaseCapitalParser()
        data = parser.parse(results)

        flows = data["capital_flows"]
        assert len(flows) == 2
        assert "2025-11-05" in flows[0]["created_at"]
        assert "2025-10-28" in flows[1]["created_at"]

    def test_deposit_and_withdraw_same_date(self):
        """同一天既有转入又有转出"""
        results = [
            _make_ocr("▲ 2025-10 净转入 +1121.00", 30, 20),
            # Deposit 1620
            _make_ocr("10-28 15:00", 100, 20),
            _make_ocr("银证转入", 100, 200),
            _make_ocr("+1620.00", 100, 400),
            # Withdraw 2500
            _make_ocr("10-28 15:00", 160, 20),
            _make_ocr("银证转出", 160, 200),
            _make_ocr("-2,500.00", 160, 400),
        ]

        parser = HuaseCapitalParser()
        data = parser.parse(results)

        flows = data["capital_flows"]
        assert len(flows) == 2
        assert flows[0]["type"] == "deposit"
        assert flows[0]["amount"] == 1620.0
        assert flows[1]["type"] == "withdraw"
        assert flows[1]["amount"] == -2500.0

    def test_version_field(self):
        parser = HuaseCapitalParser()
        data = parser.parse([])
        assert data["version"] == "1"
        assert "capital_flows" in data

    def test_parse_decimal(self):
        from decimal import Decimal
        result = HuaseCapitalParser._parse_decimal("+1,234.56")
        assert result == Decimal("1234.56")

        result = HuaseCapitalParser._parse_decimal("-500.00")
        assert result == Decimal("-500.00")

        result = HuaseCapitalParser._parse_decimal("abc")
        assert result is None
