"""StockMemos 侧边栏导航"""

import streamlit as st


def render_sidebar():
    """渲染侧边栏导航"""
    with st.sidebar:
        st.markdown("## 📈 StockMemos")
        st.divider()

        st.page_link("streamlit_app.py", label="📋 持仓概览", use_container_width=True)

        st.divider()
        st.caption("v0.2.0")
