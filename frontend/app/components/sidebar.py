"""共享侧边栏导航组件

用法：
    import sys; sys.path.append("/app")
    from app.components.sidebar import render_sidebar
    render_sidebar()
"""

import streamlit as st


def render_sidebar():
    """渲染统一侧边栏导航（所有页面共用）"""
    
    # 隐藏默认导航
    st.sidebar.markdown("""
        <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.sidebar.title("📊 StockMemos")
    
    # 页面导航
    st.sidebar.page_link("streamlit_app.py", label="📈 持仓总览")
    st.sidebar.page_link("pages/2_个股分析.py", label="🔍 个股分析")
    st.sidebar.page_link("pages/2_自选股与备忘录.py", label="📋 自选股与备忘录")
    st.sidebar.page_link("pages/3_事件时间线.py", label="📅 事件时间线")
    st.sidebar.page_link("pages/3_事件追踪.py", label="📌 事件追踪")
    st.sidebar.page_link("pages/4_策略与回测.py", label="🎯 策略与回测")
    st.sidebar.page_link("pages/4_策略配置.py", label="⚙️ 策略配置")
    st.sidebar.page_link("pages/5_设置与投递.py", label="📡 设置与投递")
    
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
