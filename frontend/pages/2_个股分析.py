"""个股分析页 — 触发AI深度分析并展示结果

功能占位：
    - 股票代码输入 + "深度分析"按钮
    - 分析进度展示（后续实现Agent状态）
    - 结果展示：多空辩论、事件影响、估值判定
"""

import streamlit as st

st.title("🔍 个股深度分析")
st.caption("AI 驱动的多Agent协作分析")

st.markdown("---")

code = st.text_input("输入股票代码", placeholder="如 000001.SZ")

if st.button("🚀 开始分析", use_container_width=True, type="primary"):
    if code:
        st.info(f"正在为 {code} 启动分析流程...")
        st.progress(10, text="DataAgent 拉取数据中...")
        # 后续集成：调用后端 /api/stock/{code}/analyze
        st.warning("Agent 分析链路正在开发中（Milestone 2）")
    else:
        st.error("请输入股票代码")

st.markdown("---")

st.markdown("""
### 分析结果将包含：

1. **最终评级** — 综合多空观点给出买入/卖出/持有建议
2. **多空辩论** — 看多Agent vs 看空Agent 的观点对比
3. **事件影响** — 重大事件对该股的预期影响评估
4. **估值判定** — 基于技术指标的估值位置（高估/合理/低估）
5. **数据摘要** — 最新行情、财务指标、资金流向
""")
