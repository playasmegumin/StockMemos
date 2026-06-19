"""FundamentalAgent — 基本面分析 Agent

职责：
- 拉取股票财务数据（TuShare）
- 调用 LLM 分析公司基本面、估值、业务前景
- 输出结构化结果，用于更新投资备忘录

输出格式（JSON）：
    {
        "target_price": 15.5,
        "valuation_method": "PE",
        "business_scope": "平安银行是中国领先的零售银行...",
        "confidence": 0.78,
        "reasoning": "分析过程..."
    }
"""

import logging
from typing import Any, Dict
from app.services.llm_router import LLMRouter
from app.services.tushare_client import TushareClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的股票基本面分析师。请基于提供的财务数据，给出以下分析结果（必须返回 JSON）：

{
    "target_price": "目标股价（数字，保留2位小数）",
    "valuation_method": "估值方法，如PE/DCF/可比公司",
    "business_scope": "业务范围、供需关系、产业链生态位的简要分析（100-300字）",
    "confidence": "置信度，0.00-1.00",
    "reasoning": "做出估值判断的核心逻辑（200-500字）"
}

注意：
1. 如果数据不足，target_price 可以为 null，confidence 设为 0.5
2. 分析必须基于实际数据，不得编造数字
3. 返回的 JSON 必须是合法格式，不要包含 Markdown 代码块
"""


class FundamentalAgent:
    """基本面分析 Agent"""

    def __init__(self, llm: LLMRouter, tushare: TushareClient) -> None:
        self._llm = llm
        self._tushare = tushare

    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """对某只股票进行基本面分析

        Returns:
            JSON 格式的分析结果，包含 target_price / valuation_method / business_scope / confidence / reasoning
        """
        logger.info("[FundamentalAgent] analyzing %s", stock_code)

        # 拉取数据
        basic = self._tushare.get_stock_basic(stock_code) or {}
        daily_basic = self._tushare.get_daily_basic(stock_code, "20240601") or {}
        kline = self._tushare.get_daily_kline(stock_code, "20240101", "20240630") or []

        # 构建 prompt
        latest_price = kline[0].get("close", "N/A") if kline else "N/A"
        pe = daily_basic.get("pe", "N/A")
        pb = daily_basic.get("pb", "N/A")
        turnover = daily_basic.get("turnover_rate", "N/A")

        data_text = f"""
股票代码：{stock_code}
基本信息：{basic}
最新收盘价：{latest_price}
PE：{pe}
PB：{pb}
换手率：{turnover}
近半年K线数据：{len(kline)} 条
"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请分析以下股票的基本面：\n{data_text}"},
        ]

        result = self._llm.chat(messages, temperature=0.5)
        if "error" in result:
            logger.error("[FundamentalAgent] LLM error: %s", result)
            return result

        # 补充 stock_code 字段
        result["stock_code"] = stock_code
        result["agent_name"] = "fundamental_agent"
        logger.info("[FundamentalAgent] done for %s", stock_code)
        return result
