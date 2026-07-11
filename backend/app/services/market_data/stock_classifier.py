"""Stock Code Classifier — 根据股票代码自动推断交易所和品种类型

用法:
    result = classify("518600")
    # → StockClassifyResult(exchange="SH", type="fund")

    result = classify("BRK.A")
    # → StockClassifyResult(exchange="US", type="stock")

设计决策（2026-07-10 团队决议）：
    用户不可手动指定交易所，全部由分类器根据代码决定。
    见 docs/stock-classifier-design.md
"""

from dataclasses import dataclass
from typing import Optional
import re


# ─── 类型定义 ───────────────────────────────────────────


@dataclass
class StockClassifyResult:
    exchange: str          # "SH" | "SZ" | "HK" | "US"
    type: str              # "stock" | "fund" | "unknown"


# ─── 已知交易所后缀 ──────────────────────────────────────

_EXCHANGE_SUFFIXES = {
    ".SH": "SH",
    ".SZ": "SZ",
    ".HK": "HK",
    ".US": "US",
}

# 中国 A 股前缀规则
# 来源：docs/identify-stock-code-CN.md
# 注意：000001 同时是"上证指数"(SH)和"平安银行"(SZ)，
#       个人投资者不会持仓指数，故归为 SZ 股票

# 个股前缀
_STOCK_PREFIXES_SH = {"600", "601", "603", "605", "688", "900"}
_STOCK_PREFIXES_SZ = {"000", "001", "002", "003", "300", "301", "200"}

# 基金前缀（ETF / LOF / 公募REITs）
_FUND_PREFIXES_SH = {
    "510", "511", "512", "513", "515", "517", "518",
    "520", "530", "560", "561", "562", "563", "588",
}
_FUND_PREFIXES_SZ = {
    "158", "159",
    "160", "161", "162", "163", "164", "165", "166", "167", "168", "169",
    "184",
    "180", "181",
}


# ─── 主分类函数 ─────────────────────────────────────────


def classify(symbol: str) -> StockClassifyResult:
    """根据股票代码推断交易所和品种类型。

    处理流程:
        1. 若输入为 {纯数字}.{字母} 形式（如 518600.SZ）→ 剥离后缀，用纯代码分类
        2. 含字母 → US（BRK.A、DRAM 等）
        3. 纯数字且 len=6 → CN（按前缀表）
        4. 纯数字且 len<6 → HK
        5. 其余 → unknown

    注意:
        后缀仅用于剥离，交易所全部由分类器根据纯代码自行推导。
        即使输入 518600.SZ，分类器仍返回 SH/fund（因为 518600 是上交所 ETF）。
    """
    code, _ = _strip_suffix(symbol)
    return _classify_code(code)


def _strip_suffix(raw: str) -> tuple[str, Optional[str]]:
    """剥离已知交易所后缀 (.SH .SZ .HK .US)，大小写不敏感。

    只对 {纯数字}.{字母} 形式生效（如 518600.SZ  →  518600.suffix=SZ），
    否则整体保留（如 BRK.A 不会被拆分）。

    注意：
        剥离后的 suffix 仅用于辅助信息，分类器以纯代码的推导结果为准。
    """
    # 检查是否为 {纯数字}.{字母} 形式
    m = re.match(r'^(\d+)\.([A-Za-z]{2,})$', raw)
    if m:
        code = m.group(1)
        suffix = f".{m.group(2).upper()}"
        if suffix in _EXCHANGE_SUFFIXES:
            return code, _EXCHANGE_SUFFIXES[suffix]
    return raw, None


def _classify_code(code: str) -> StockClassifyResult:
    """对纯代码进行分类（不含后缀）。"""
    if not code:
        return StockClassifyResult(exchange="", type="unknown")

    # 含字母 → US
    if re.search(r'[A-Za-z]', code):
        return StockClassifyResult(exchange="US", type="stock")

    # 纯数字
    if code.isdigit():
        length = len(code)

        # 6位 → CN（按前缀规则）
        if length == 6:
            return _classify_cn(code)

        # 小于6位 → HK
        if length < 6:
            return StockClassifyResult(exchange="HK", type="stock")

    # 其余 → unknown
    return StockClassifyResult(exchange="", type="unknown")


def _classify_cn(code: str) -> StockClassifyResult:
    """对中国 6 位代码进行前缀匹配，区分 stock/fund/unknown。

    边界说明（2026-07-10）：
        000001 同时是"上证指数"(SH)和"平安银行"(SZ)。
        个人投资者不会持仓指数，故归为 SZ+股票。
        如需支持指数等品种，请扩展前缀表或添加额外判断逻辑。
    """
    prefix3 = code[:3]
    prefix4 = code[:4]

    # 基金优先（因为基金前缀比个股更具体）
    if prefix3 in _FUND_PREFIXES_SH or prefix4 in _FUND_PREFIXES_SH:
        return StockClassifyResult(exchange="SH", type="fund")
    if prefix3 in _FUND_PREFIXES_SZ:
        return StockClassifyResult(exchange="SZ", type="fund")

    # 个股
    if prefix3 in _STOCK_PREFIXES_SH:
        return StockClassifyResult(exchange="SH", type="stock")
    if prefix3 in _STOCK_PREFIXES_SZ:
        return StockClassifyResult(exchange="SZ", type="stock")

    # 北交所
    if prefix3 in {"830", "831", "832", "833", "834", "835", "836",
                    "837", "838", "839", "870", "871", "872", "873",
                    "874", "875", "876", "877", "878", "879",
                    "880", "881", "882", "883", "884", "885", "886",
                    "887", "888", "889",
                    "920", "921", "922"}:
        return StockClassifyResult(exchange="BJ", type="stock")

    # 无法识别（债券 / 指数 / 其他）
    return StockClassifyResult(exchange="", type="unknown")
