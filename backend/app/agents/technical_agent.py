"""TechnicalAgent — 交易数据分析 Agent

职责：
- 拉取历史 K 线数据（TuShare）
- 分析价格走势、成交量、技术指标
- 输出趋势判断（短线/中线/长期）

输出格式（JSON）：
    {
        "short_trend": "up/down/sideways",
        "mid_trend": "up/down/sideways",
        "long_trend": "up/down/sideways",
        "trend_logic": "趋势判断核心逻辑...",
        "key_levels": {"support": "...", "resistance": "..."},
        "confidence": 0.0-1.0,
        "reasoning": "分析过程"
    }
"""

import logging
from typing import Any, Dict
from app.services.llm_router import LLMRouter
from app.services.tushare_client import TushareClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的技术分析专家。请基于提供的K线数据，给出趋势判断（必须返回 JSON）：

{
    "short_trend": "短线趋势：up/down/sideways",
    "mid_trend": "中线趋势：up/down/sideways",
    "long_trend": "长期趋势：up/down/sideways",
    "trend_logic": "趋势判断核心逻辑（200-400字）",
    "key_levels": {"support": "支撑位", "resistance": "阻力位"},
    "confidence": "置信度 0.00-1.00",
    "reasoning": "分析过程"
}

注意：
1. 分析必须基于实际价格数据
2. 趋势判断要考虑成交量配合
3. 返回的 JSON 必须是合法格式
"""


class TechnicalAgent:
    """交易数据分析 Agent"""

    def __init__(self, llm: LLMRouter, tushare: TushareClient) -> None:
        self._llm = llm
        self._tushare = tushare

    def analyze(self, stock_code: str) -> Dict[str, Any]:
        """对某只股票进行技术分析

        Returns:
            JSON 包含 short_trend / mid_trend / long_trend / trend_logic / key_levels / confidence
        """
        logger.info("[TechnicalAgent] analyzing %s", stock_code)

        # 拉取近一年数据
        kline = self._tushare.get_daily_kline(stock_code, "20240101", "20241231") or []
        if not kline:
            return {"error": "无法获取K线数据", "stock_code": stock_code}

        # 提取关键数据点（避免 prompt 过长，只取最近20条 + 统计信息）
        recent = kline[:20]
        prices = [float(r.get("close", 0)) for r in kline if r.get("close")]
        volumes = [float(r.get("vol", 0)) for r in kline if r.get("vol")]

        avg_price = sum(prices) / len(prices) if prices else 0
        max_price = max(prices) if prices else 0
        min_price = min(prices) if prices else 0
        avg_volume = sum(volumes) / len(volumes) if volumes else 0

        data_text = f"""
股票代码：{stock_code}
数据时间范围：2024-01-01 至 2024-12-31
K线数据条数：{len(kline)}
最新20日数据摘要：{recent}

统计指标：
- 平均收盘价：{avg_price:.2f}
- 最高价：{max_price:.2f}
- 最低价：{min_price:.2f}
- 平均成交量：{avg_volume:.0f}
"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请分析以下股票的技术面：\n{data_text}"},
        ]

        result = self._llm.chat(messages, temperature=0.5)
        if "error" in result:
            logger.error("[TechnicalAgent] LLM error: %s", result)
            return result

        result["stock_code"] = stock_code
        result["agent_name"] = "technical_agent"
        logger.info("[TechnicalAgent] done for %s", stock_code)
        return result
