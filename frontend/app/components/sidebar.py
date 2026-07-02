"""StockMemos 侧边栏导航"""

import streamlit as st


def render_sidebar():
    """渲染侧边栏导航"""
    with st.sidebar:
        st.markdown("## 📈 StockMemos")
        st.divider()

        st.page_link("streamlit_app.py", label="📋 持仓概览", use_container_width=True)
        st.page_link("streamlit_app.py", label="📋 股票列表", use_container_width=True)

        st.divider()
        st.caption(f"v0.2.0 · {st.session_state.get('page', 'home')}")
