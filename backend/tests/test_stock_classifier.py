"""Tests for stock_classifier.py"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from app.services.market_data.stock_classifier import classify, StockClassifyResult


# ─── 中国 A 股个股 ───────────────────────────────────


class TestClassifyCNStock:
    def test_sh_mainboard(self):
        """600/601/603/605 → SH stock"""
        for code in ["600519", "601318", "603259", "605117"]:
            r = classify(code)
            assert r == StockClassifyResult(exchange="SH", type="stock"), f"failed for {code}"

    def test_sh_star_market(self):
        """688 → SH stock (科创板)"""
        r = classify("688981")
        assert r == StockClassifyResult(exchange="SH", type="stock")

    def test_sz_mainboard(self):
        """000/001/002 → SZ stock"""
        for code in ["000001", "001234"]:
            r = classify(code)
            assert r == StockClassifyResult(exchange="SZ", type="stock"), f"failed for {code}"

    def test_sz_chinext(self):
        """300 → SZ stock (创业板)"""
        r = classify("300750")
        assert r == StockClassifyResult(exchange="SZ", type="stock")


# ─── 中国基金/ETF ─────────────────────────────────────


class TestClassifyCNFund:
    def test_sh_etf(self):
        """510/513/518/588 → SH fund"""
        for code in ["518600", "513100", "510050", "588000"]:
            r = classify(code)
            assert r == StockClassifyResult(exchange="SH", type="fund"), f"failed for {code}"

    def test_sz_etf(self):
        """159 → SZ fund"""
        r = classify("159915")
        assert r == StockClassifyResult(exchange="SZ", type="fund")

    def test_sz_lof(self):
        """160-169 → SZ fund (LOF)"""
        for code in ["160706", "163406"]:
            r = classify(code)
            assert r == StockClassifyResult(exchange="SZ", type="fund"), f"failed for {code}"

    def test_sz_reit(self):
        """180/181 → SZ fund (公募REITs)"""
        r = classify("180801")
        assert r == StockClassifyResult(exchange="SZ", type="fund")


# ─── 港股 ────────────────────────────────────────────


class TestClassifyHK:
    def test_hk_5digit(self):
        """4位纯数字 → HK"""
        r = classify("07709")
        assert r == StockClassifyResult(exchange="HK", type="stock")

    def test_hk_4digit(self):
        """4位纯数字 → HK"""
        r = classify("7000")
        assert r == StockClassifyResult(exchange="HK", type="stock")

    def test_hk_3digit(self):
        """3位纯数字 → HK"""
        r = classify("005")
        r2 = classify("5")
        assert r.exchange == "HK"
        assert r2.exchange == "HK"

    def test_hk_with_suffix(self):
        """07515.HK → HK stock"""
        r = classify("07515.HK")
        assert r == StockClassifyResult(exchange="HK", type="stock")


# ─── 美股 ────────────────────────────────────────────


class TestClassifyUS:
    def test_us_etf(self):
        """纯字母 → US stock"""
        for code in ["DRAM", "SPY", "QQQ", "GLD"]:
            r = classify(code)
            assert r == StockClassifyResult(exchange="US", type="stock"), f"failed for {code}"

    def test_us_with_dot(self):
        """BRK.A → US stock (含点但不是 {数字}.{字母} 模式)"""
        r = classify("BRK.A")
        assert r == StockClassifyResult(exchange="US", type="stock")


# ─── 后缀剥离 ─────────────────────────────────────────


class TestSuffixStripping:
    def test_sh_suffix(self):
        """518600.SH → SH fund (后缀不影响分类器结果)"""
        r = classify("518600.SH")
        assert r == StockClassifyResult(exchange="SH", type="fund")

    def test_sz_suffix(self):
        """518000.SZ → SH fund（后缀不覆盖，分类器以纯代码为准）"""
        r = classify("518000.SZ")
        assert r.exchange == "SH"  # 分类器自身判断为 SH/fund

    def test_wrong_suffix(self):
        """000001.SH → SZ stock（用户写下 SH 后缀，分类器仍正确返回 SZ）"""
        r = classify("000001.SH")
        assert r == StockClassifyResult(exchange="SZ", type="stock")

    def test_hk_suffix(self):
        """07515.HK → HK"""
        assert classify("07515.HK").exchange == "HK"

    def test_us_suffix(self):
        """AAPL.US → US"""
        assert classify("AAPL.US").exchange == "US"

    def test_lowercase_suffix(self):
        """518600.sh → SH（大小写不敏感）"""
        assert classify("518600.sh").exchange == "SH"

    def test_dot_not_number(self):
        """BRK.A 不是 {数字}.{字母} 模式，整体作为美股"""
        assert classify("BRK.A").exchange == "US"
        assert classify("BRK.A").type == "stock"


# ─── 边界/异常情况 ────────────────────────────────────


class TestClassifyEdge:
    def test_unknown_bond(self):
        """可转债/国债等 → unknown"""
        for code in ["110052", "019547", "010107"]:
            r = classify(code)
            assert r.type == "unknown", f"failed for {code}"

    def test_empty(self):
        """空字符串 → empty exchange, unknown type"""
        r = classify("")
        assert r.type == "unknown"

    def test_000001_ambiguity(self):
        """000001 同时是上证指数(SH)和平安银行(SZ) → 归为 SZ stock"""
        r = classify("000001")
        assert r == StockClassifyResult(exchange="SZ", type="stock")
