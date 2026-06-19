"""事件追踪页 — 管理重大事件并查看个股影响

功能占位：
    - 事件列表（时间线视图）
    - 新增事件表单
    - 事件与个股关联展示
"""

import sys
sys.path.append("/app")
from app.components.sidebar import render_sidebar


import streamlit as st
from datetime import datetime

# ── 全局 CSS：页面宽度完全铺满（每个页面独立注入）──
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


st.title("📅 事件追踪")
st.caption("跟踪重大事件对持仓的影响")

st.markdown("---")

with st.expander("➕ 添加新事件"):
    with st.form("new_event"):
        c1, c2 = st.columns(2)
        name = c1.text_input("事件名称", placeholder="如 美联储利率决议")
        category = c2.selectbox(
            "事件类型",
            ["monetary_policy", "geopolitical", "macro_data", "company_event"],
        )
        expected_date = st.date_input("预期日期", value=datetime.today())
        description = st.text_area("事件描述")
        submitted = st.form_submit_button("保存事件")
        if submitted:
            st.info("事件保存功能开发中（Milestone 3）")

st.markdown("---")

st.subheader("📋 事件列表")
st.info("暂无事件记录。请使用上方表单添加。")

st.markdown("""
### 事件类型说明：
- **monetary_policy** — 货币政策（如美联储利率决议、降准）
- **geopolitical** — 地缘政治（如战争、贸易摩擦）
- **macro_data** — 宏观经济数据（如GDP、CPI、PMI）
- **company_event** — 公司事件（如财报、分红、并购）
""")
