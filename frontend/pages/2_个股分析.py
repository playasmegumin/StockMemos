"""个股分析页 — 触发AI深度分析并展示结果

功能：
    - 股票代码输入 + "深度分析"按钮
    - 分析进度展示（Fundamental/News/Technical Agent）
    - 结果展示：多标签页展示多空辩论、事件影响、估值判定
"""

import sys
sys.path.append("/app")
from app.components.sidebar import render_sidebar

import requests
import streamlit as st

API_BASE = "http://backend:8080/api"

st.set_page_config(
    page_title="个股分析",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 全局 CSS ─────────────────────────────
st.markdown("""
    <style>
    .stApp .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    [data-testid="stSidebar"] {
        width: 16rem !important;
        min-width: 16rem !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .stDataFrame td {
        white-space: nowrap !important;
    }
    </style>
""", unsafe_allow_html=True)

render_sidebar()


def _api(method: str, path: str, **kwargs):
    """统一 API 调用"""
    url = f"{API_BASE}{path}"
    try:
        resp = requests.request(method, url, timeout=120, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API 请求失败: {e}")
        return None


def _is_a_share(code: str) -> bool:
    """判断是否为 A 股"""
    return code.endswith(".SZ") or code.endswith(".SH") or code.endswith(".BJ")


# ── 页面标题 ─────────────────────────────
st.title("🔍 个股深度分析")
st.caption("AI 驱动的多Agent协作分析")
st.markdown("---")

# ── 自动填充：从持仓总览跳转 ──────────────
auto_code = st.session_state.get("analyze_stock_code", "")
if auto_code:
    st.info(f"📌 从持仓总览跳转：正在分析 {auto_code}")
    code = st.text_input("输入股票代码", value=auto_code)
    # 清除 session_state 避免重复触发
    del st.session_state["analyze_stock_code"]
else:
    code = st.text_input("输入股票代码", placeholder="如 000001.SZ")

# 市场类型提示
if code and not _is_a_share(code):
    st.warning(f"⚠️ {code} 看起来是非 A 股代码。当前 Agent 分析主要支持 A 股（TuShare 数据源），其他市场可能数据不完整。")

if st.button("🚀 开始分析", use_container_width=True, type="primary"):
    if not code:
        st.error("请输入股票代码")
        st.stop()

    # 检查是否已在自选股（如果不在需要先添加）
    with st.spinner("检查自选股..."):
        watchlist = _api("GET", "/watchlist") or []
        in_watchlist = any(w.get("stock_code") == code for w in watchlist)
    
    if not in_watchlist:
        st.warning(f"⚠️ {code} 不在自选股中，Agent 分析需要先添加。正在自动添加...")
        # 尝试添加（stock_name 未知，先留空）
        _api("POST", "/watchlist", json={
            "stock_code": code,
            "stock_name": None,
            "sector": None,
        })
        st.info("已添加，正在启动分析...")

    # 创建三个 Agent 结果占位
    fundamental_result = None
    news_result = None
    technical_result = None

    # 1. FundamentalAgent
    with st.status("🔍 FundamentalAgent 分析中...", expanded=True) as status:
        fundamental_result = _api("POST", f"/analyze/{code}/fundamental")
        if fundamental_result and fundamental_result.get("status") == "success":
            status.update(label="✅ FundamentalAgent 完成", state="complete")
        else:
            status.update(label="⚠️ FundamentalAgent 失败", state="error")
    
    # 2. NewsAgent
    with st.status("📰 NewsAgent 分析中（多空辩论）...", expanded=True) as status:
        news_result = _api("POST", f"/analyze/{code}/news")
        if news_result and news_result.get("status") == "success":
            status.update(label="✅ NewsAgent 完成", state="complete")
        else:
            status.update(label="⚠️ NewsAgent 失败", state="error")
    
    # 3. TechnicalAgent
    with st.status("📈 TechnicalAgent 分析中...", expanded=True) as status:
        technical_result = _api("POST", f"/analyze/{code}/technical")
        if technical_result and technical_result.get("status") == "success":
            status.update(label="✅ TechnicalAgent 完成", state="complete")
        else:
            status.update(label="⚠️ TechnicalAgent 失败", state="error")

    # ── 多标签页展示结果 ───────────────────
    st.markdown("---")
    st.subheader("📊 分析结果")
    
    tabs = st.tabs(["💰 基本面", "📰 消息多空辩论", "📈 技术分析", "📝 提示词"])
    
    # Tab 1: 基本面
    with tabs[0]:
        if fundamental_result and fundamental_result.get("status") == "success":
            r = fundamental_result.get("result", {})
            c1, c2, c3 = st.columns(3)
            c1.metric("估值方法", r.get("valuation_method", "N/A"))
            c2.metric("目标价", f"¥{r.get('target_price', 'N/A')}" if r.get("target_price") else "N/A")
            c3.metric("置信度", f"{r.get('confidence', 'N/A')}")
            st.markdown("**业务分析**:")
            st.markdown(r.get("business_scope", "无") or "无")
            st.markdown("**分析逻辑**:")
            st.markdown(r.get("reasoning", "无") or "无")
        else:
            st.error("FundamentalAgent 分析失败或未完成")
    
    # Tab 2: 消息多空辩论
    with tabs[1]:
        if news_result and news_result.get("status") == "success":
            r = news_result.get("result", {})
            
            st.markdown(f"**综合判断**: {r.get('consensus', 'N/A')}")
            st.markdown(f"**推荐**: {r.get('recommendation', 'N/A')}")
            
            st.markdown("---")
            
            bull = r.get("bull_case", {})
            bear = r.get("bear_case", {})
            
            col_bull, col_bear = st.columns(2)
            with col_bull:
                st.markdown("### 🟢 看多观点")
                for arg in bull.get("arguments", []):
                    st.markdown(f"- {arg}")
                st.markdown(f"*置信度: {bull.get('confidence', 'N/A')}*")
            with col_bear:
                st.markdown("### 🔴 看空观点")
                for arg in bear.get("arguments", []):
                    st.markdown(f"- {arg}")
                st.markdown(f"*置信度: {bear.get('confidence', 'N/A')}*")
            
            st.markdown("---")
            st.markdown("**事件列表**:")
            for ev in r.get("events", []):
                tag_color = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(ev.get("impact_tag"), "⚪")
                st.markdown(f"- {tag_color} **{ev.get('name')}** ({ev.get('expected_date', '待定')})")
            
            st.markdown("**分析逻辑**:")
            st.markdown(r.get("reasoning", "无") or "无")
        else:
            st.error("NewsAgent 分析失败或未完成")
    
    # Tab 3: 技术分析
    with tabs[2]:
        if technical_result and technical_result.get("status") == "success":
            r = technical_result.get("result", {})
            c1, c2, c3 = st.columns(3)
            c1.metric("短线趋势", r.get("short_trend", "N/A"))
            c2.metric("中线趋势", r.get("mid_trend", "N/A"))
            c3.metric("长期趋势", r.get("long_trend", "N/A"))
            c4, c5 = st.columns(2)
            c4.metric("支撑位", r.get("key_levels", {}).get("support", "N/A"))
            c5.metric("阻力位", r.get("key_levels", {}).get("resistance", "N/A"))
            st.markdown("**趋势逻辑**:")
            st.markdown(r.get("trend_logic", "无") or "无")
        else:
            st.error("TechnicalAgent 分析失败或未完成")
    
    # Tab 4: 提示词
    with tabs[3]:
        st.markdown("### FundamentalAgent 提示词")
        st.code("""你是一个专业的股票基本面分析师。请基于提供的财务数据，给出以下分析结果（必须返回 JSON）：
{
    "target_price": "目标股价（数字，保留2位小数）",
    "valuation_method": "估值方法，如PE/DCF/可比公司",
    "business_scope": "业务范围、供需关系、产业链生态位的简要分析（100-300字）",
    "confidence": "置信度，0.00-1.00",
    "reasoning": "做出估值判断的核心逻辑（200-500字）"
}""", language="json")
        
        st.markdown("### NewsBullAgent 提示词")
        st.code("""你是一个乐观派股票分析师。请基于已知信息，从看多角度分析股票。列出所有潜在的利好因素和催化剂。必须返回 JSON：
{"arguments": ["看多理由1", "看多理由2"], "confidence": 0.0-1.0, "reasoning": "分析过程"}""", language="json")
        
        st.markdown("### NewsBearAgent 提示词")
        st.code("""你是一个谨慎派股票分析师。请基于已知信息，从看空角度分析股票。列出所有潜在的风险因素和利空催化剂。必须返回 JSON：
{"arguments": ["看空理由1", "看空理由2"], "confidence": 0.0-1.0, "reasoning": "分析过程"}""", language="json")
        
        st.markdown("### NewsRefereeAgent 提示词")
        st.code("""你是一个中立的裁判分析师。请综合看多和看空观点，给出客观的综合判断。必须返回 JSON：
{
    "events": [{"name": "事件名", "impact_tag": "bullish/bearish/neutral", "expected_date": "YYYY-MM-DD", "reasoning": "..."}],
    "consensus": "综合判断",
    "recommendation": "buy/hold/sell/watch",
    "reasoning": "分析过程"
}""", language="json")
        
        st.markdown("### TechnicalAgent 提示词")
        st.code("""你是一个专业的技术分析专家。请基于提供的K线数据，给出趋势判断（必须返回 JSON）：
{
    "short_trend": "短线趋势：up/down/sideways",
    "mid_trend": "中线趋势：up/down/sideways",
    "long_trend": "长期趋势：up/down/sideways",
    "trend_logic": "趋势判断核心逻辑（200-400字）",
    "key_levels": {"support": "支撑位", "resistance": "阻力位"},
    "confidence": "置信度 0.00-1.00",
    "reasoning": "分析过程"
}""", language="json")
