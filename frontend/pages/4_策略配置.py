"""策略配置与回测页 — 定义策略并运行回测

功能占位：
    - 策略列表（启用/停用）
    - 新建策略表单
    - 策略运行结果展示
    - 回测入口
"""

import streamlit as st

st.title("⚙️ 策略与回测")
st.caption("自定义技术指标策略并验证历史表现")

st.markdown("---")

# 策略列表
st.subheader("📋 策略列表")

st.info("暂无策略。请使用下方表单添加。")

st.markdown("---")

with st.expander("➕ 新建策略"):
    with st.form("new_strategy"):
        name = st.text_input("策略名称", placeholder="如 PE<20 且 MA120上方")
        description = st.text_area("策略描述")
        st.markdown("策略规则（JSON 格式）：")
        st.code('''{
    "conditions": [
        {"indicator": "PE", "operator": "<", "value": 20},
        {"indicator": "MA120", "operator": "above", "reference": "close"}
    ]
}''', language="json")
        submitted = st.form_submit_button("保存策略")
        if submitted:
            st.info("策略保存功能开发中（Milestone 4）")

st.markdown("---")

# 回测入口
st.subheader("📈 回测验证")

st.markdown("选择股票 + 策略 + 时间区间，运行历史回测。")

c1, c2, c3 = st.columns(3)
stock_code = c1.text_input("股票代码", placeholder="000001.SZ")
strategy_id = c2.text_input("策略ID")
date_range = c3.date_input("时间区间", value=[])

if st.button("▶️ 运行回测", use_container_width=True, type="primary"):
    st.info("回测功能开发中（Milestone 4）")

st.markdown("""
### 回测结果将包含：

1. **收益曲线** — 策略 vs 基准的累计收益对比
2. **统计指标** — 总收益率、最大回撤、夏普比率
3. **交易记录** — 每次买入/卖出的时间、价格、理由
""")
