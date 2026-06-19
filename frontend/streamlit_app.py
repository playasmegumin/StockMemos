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

# ── 全局 CSS：页面宽度完全铺满 ─────────────────
st.markdown("""
    <style>
    /* 主内容区：移除最大宽度限制，完全铺满 */
    .stApp .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    /* 侧边栏收窄（默认 21rem=336px 太宽） */
    [data-testid="stSidebar"] {
        width: 16rem !important;
        min-width: 16rem !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    /* 表格不换行 */
    .stDataFrame td {
        white-space: nowrap !important;
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
