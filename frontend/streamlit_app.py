"""Streamlit 主入口 — 设置页面全局配置和侧边栏导航

页面结构（通过 pages/ 目录自动路由）：
    1_持仓总览.py — 首页 Dashboard
    2_个股分析.py — 股票深度分析
    3_事件追踪.py — 事件管理
    4_策略配置.py — 策略与回测
"""

import streamlit as st

st.set_page_config(
    page_title="StockMemos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 全局 CSS：页面宽度铺满 ─────────────────
st.markdown("""
    <style>
    .main .block-container {
        max-width: 100%;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    .stDataFrame td {
        white-space: nowrap;
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("📊 StockMemos")
st.sidebar.markdown("---")

st.sidebar.markdown("""
**多Agent智能投研系统**

- 持仓跟踪与盈亏分析
- AI 驱动的多空辩论
- 事件影响评估
- 策略回测与信号
""")

st.sidebar.markdown("---")
st.sidebar.caption("Backend: http://backend:8080")
