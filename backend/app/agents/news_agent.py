"""NewsAgent — 网络消息分析 Agent（含多空辩论）

职责：
- 分析股票相关消息（基于 TuShare 数据 + LLM 推理）
- 内部包含 3 个子 Agent：NewsBullAgent / NewsBearAgent / NewsRefereeAgent
- 输出结构化事件列表 + 多空观点

输出格式（JSON）：
    {
        "events": [
            {"name": "事件名", "impact_tag": "bullish/bearish/neutral", "expected_date": "YYYY-MM-DD", "reasoning": "..."}
        ],
        "bull_case": "看多理由",
        "bear_case": "看空理由",
        "consensus": "综合判断",
        "reasoning": "分析过程"
    }
"""

import logging
from typing import Any, Dict, List
from app.services.llm_router import LLMRouter

logger = logging.getLogger(__name__)

BULL_SYSTEM_PROMPT = """你是一个乐观派股票分析师。请基于已知信息，从看多角度分析股票。列出所有潜在的利好因素和催化剂。必须返回 JSON：
{"arguments": ["看多理由1", "看多理由2"], "confidence": 0.0-1.0, "reasoning": "分析过程"}"""

BEAR_SYSTEM_PROMPT = """你是一个谨慎派股票分析师。请基于已知信息，从看空角度分析股票。列出所有潜在的风险因素和利空催化剂。必须返回 JSON：
{"arguments": ["看空理由1", "看空理由2"], "confidence": 0.0-1.0, "reasoning": "分析过程"}"""

REFEREE_SYSTEM_PROMPT = """你是一个中立的裁判分析师。请综合看多和看空观点，给出客观的综合判断。必须返回 JSON：
{
    "events": [{"name": "事件名", "impact_tag": "bullish/bearish/neutral", "expected_date": "YYYY-MM-DD", "reasoning": "..."}],
    "consensus": "综合判断",
    "recommendation": "buy/hold/sell/watch",
    "reasoning": "分析过程"
}"""


class NewsAgent:
    """消息分析 Agent（内部含多空辩论）"""

    def __init__(self, llm: LLMRouter) -> None:
        self._llm = llm

    def analyze(self, stock_code: str, stock_name: str = "") -> Dict[str, Any]:
        """对某只股票进行消息分析（多空辩论）

        Returns:
            JSON 包含 events / bull_case / bear_case / consensus / reasoning
        """
        logger.info("[NewsAgent] analyzing %s", stock_code)

        # 第1步：NewsBullAgent
        bull_result = self._llm.chat([
            {"role": "system", "content": BULL_SYSTEM_PROMPT},
            {"role": "user", "content": f"请分析股票 {stock_code} {stock_name} 的看多因素"},
        ], temperature=0.7)

        # 第2步：NewsBearAgent
        bear_result = self._llm.chat([
            {"role": "system", "content": BEAR_SYSTEM_PROMPT},
            {"role": "user", "content": f"请分析股票 {stock_code} {stock_name} 的看空因素"},
        ], temperature=0.7)

        # 第3步：NewsRefereeAgent
        referee_input = f"""
看多观点：{bull_result}
看空观点：{bear_result}
请综合以上观点，给出最终判断。
"""
        referee_result = self._llm.chat([
            {"role": "system", "content": REFEREE_SYSTEM_PROMPT},
            {"role": "user", "content": referee_input},
        ], temperature=0.3)

        if "error" in referee_result:
            logger.error("[NewsAgent] LLM error: %s", referee_result)
            return referee_result

        # 整合所有子 Agent 输出
        result = {
            "stock_code": stock_code,
            "agent_name": "news_agent",
            "bull_case": bull_result,
            "bear_case": bear_result,
            "consensus": referee_result.get("consensus", ""),
            "events": referee_result.get("events", []),
            "recommendation": referee_result.get("recommendation", "watch"),
            "reasoning": referee_result.get("reasoning", ""),
        }
        logger.info("[NewsAgent] done for %s", stock_code)
        return result
