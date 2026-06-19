"""RSS/结构化报告输出服务

将投资备忘录、策略信号、Agent 分析结果生成为结构化报告（Markdown / JSON / RSS XML）。

支持输出格式：
- markdown: 人类可读的投研日报
- json: 结构化数据，供其他系统消费
- rss: 标准 RSS 2.0 XML，供 RSS 阅读器订阅
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from xml.sax.saxutils import escape as xml_escape

logger = logging.getLogger(__name__)


def _now_rfc822() -> str:
    """RFC 822 格式日期（RSS 标准）"""
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def generate_memo_report(memos: List[Dict[str, Any]], watchlist: List[Dict[str, Any]], format: str = "markdown") -> str:
    """生成自选股备忘录报告

    Args:
        memos: 投资备忘录列表（来自 DB 或 API）
        watchlist: 自选股列表（补充股票名称）
        format: 输出格式 markdown / json / rss

    Returns:
        格式化后的报告字符串
    """
    # 构建 stock_name 映射
    name_map = {w["stock_code"]: w.get("stock_name", "") for w in watchlist}

    if format == "json":
        return json.dumps({
            "generated_at": _now_iso(),
            "type": "investment_memo_report",
            "count": len(memos),
            "memos": memos,
        }, ensure_ascii=False, indent=2)

    if format == "rss":
        items = []
        for m in memos:
            code = m.get("stock_code", "")
            name = name_map.get(code, code)
            title = f"{name} ({code}) 备忘录更新"
            desc = _memo_to_description(m)
            items.append(f"""
    <item>
      <title>{xml_escape(title)}</title>
      <link>http://localhost:8501/自选股与备忘录</link>
      <description>{xml_escape(desc)}</description>
      <pubDate>{_now_rfc822()}</pubDate>
      <guid>{m.get('id', '')}</guid>
    </item>""")

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>StockMemos — 自选股备忘录</title>
    <link>http://localhost:8501</link>
    <description>基于多Agent协作的智能投研备忘录 RSS 订阅</description>
    <language>zh-CN</language>
    <lastBuildDate>{_now_rfc822()}</lastBuildDate>
    {''.join(items)}
  </channel>
</rss>"""

    # markdown (default)
    lines = [
        f"# 📊 投研日报 — 自选股备忘录",
        f"",
        f"**生成时间**: {_now_iso()}",
        f"**股票数量**: {len(memos)}",
        f"",
        "---",
        "",
    ]
    for m in memos:
        code = m.get("stock_code", "")
        name = name_map.get(code, code)
        lines.append(f"## {name} ({code})")
        lines.append("")
        if m.get("target_price"):
            lines.append(f"- **目标价**: ¥{m['target_price']:.2f} ({m.get('valuation_method', 'N/A')})")
        if m.get("business_scope"):
            lines.append(f"- **业务分析**: {m['business_scope'][:200]}...")
        if m.get("short_trend") or m.get("mid_trend") or m.get("long_trend"):
            lines.append(f"- **趋势**: 短 {m.get('short_trend', '?')} / 中 {m.get('mid_trend', '?')} / 长 {m.get('long_trend', '?')}")
        if m.get("trend_logic"):
            lines.append(f"- **趋势逻辑**: {m['trend_logic'][:150]}...")
        if m.get("notes"):
            lines.append(f"- **备注**: {m['notes'][:100]}...")
        lines.append(f"- **最后更新**: {m.get('last_updated_by', 'user')}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _memo_to_description(m: Dict[str, Any]) -> str:
    """将备忘录转为 RSS description 纯文本"""
    parts = []
    if m.get("target_price"):
        parts.append(f"目标价: ¥{m['target_price']:.2f}")
    if m.get("short_trend"):
        parts.append(f"趋势: {m['short_trend']}/{m.get('mid_trend', '?')}/{m.get('long_trend', '?')}")
    if m.get("trend_logic"):
        parts.append(m["trend_logic"][:200])
    return " | ".join(parts) if parts else "备忘录已更新"


def generate_strategy_report(signals: List[Dict[str, Any]], strategies: List[Dict[str, Any]], format: str = "markdown") -> str:
    """生成策略信号报告"""
    strategy_map = {s["id"]: s.get("name", "") for s in strategies}

    if format == "json":
        return json.dumps({
            "generated_at": _now_iso(),
            "type": "strategy_signal_report",
            "count": len(signals),
            "signals": signals,
        }, ensure_ascii=False, indent=2)

    if format == "rss":
        items = []
        for s in signals:
            title = f"{strategy_map.get(s.get('strategy_id', ''), '策略')} — {s.get('stock_code', '')} 信号: {s.get('signal_type', 'hold').upper()}"
            desc = f"信号日期: {s.get('signal_date', 'N/A')} | 策略: {strategy_map.get(s.get('strategy_id', ''), 'N/A')}"
            items.append(f"""
    <item>
      <title>{xml_escape(title)}</title>
      <link>http://localhost:8501/策略与回测</link>
      <description>{xml_escape(desc)}</description>
      <pubDate>{_now_rfc822()}</pubDate>
      <guid>{s.get('id', '')}</guid>
    </item>""")

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>StockMemos — 策略信号</title>
    <link>http://localhost:8501</link>
    <description>策略交易信号 RSS 订阅</description>
    <language>zh-CN</language>
    <lastBuildDate>{_now_rfc822()}</lastBuildDate>
    {''.join(items)}
  </channel>
</rss>"""

    lines = [
        f"# 🎯 策略信号日报",
        f"",
        f"**生成时间**: {_now_iso()}",
        f"**信号数量**: {len(signals)}",
        f"",
        "---",
        "",
    ]
    for s in signals:
        sig_type = s.get("signal_type", "hold")
        icon = {"buy": "🟢", "sell": "🔴", "hold": "⚪"}.get(sig_type, "⚪")
        lines.append(f"## {icon} {s.get('stock_code', 'N/A')} | {strategy_map.get(s.get('strategy_id', ''), '策略')} | {sig_type.upper()}")
        lines.append(f"- **信号日期**: {s.get('signal_date', 'N/A')}")
        if s.get("raw_data"):
            lines.append(f"- **指标数据**: {json.dumps(s['raw_data'], ensure_ascii=False)}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
