"""策略与回测页

功能：
    1. 策略列表（启用/停用、删除）
    2. 新建策略（预设模板 + 自定义规则）
    3. 回测入口：选择股票 + 策略 + 时间区间
    4. 回测结果展示：收益曲线、交易记录、关键指标
"""

import requests
import streamlit as st
import json

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

API_BASE = "http://backend:8080/api"


def _api(method: str, path: str, **kwargs):
    """统一 API 调用"""
    url = f"{API_BASE}{path}"
    try:
        resp = requests.request(method, url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API 请求失败: {e}")
        return None


# ── 页面标题 ───────────────────────────────
st.title("🎯 策略与回测")
st.caption("定义技术指标策略，执行历史回测验证")

# ── 布局：左侧策略列表 + 右侧回测 ─────────────
left, right = st.columns([1, 2])

# ════════════════════════════════════════════
# 左侧：策略列表
# ════════════════════════════════════════════
with left:
    st.subheader("📋 策略列表")
    
    # 新建策略
    with st.expander("➕ 新建策略"):
        with st.form("create_strategy"):
            name = st.text_input("策略名称", placeholder="如 均线金叉策略")
            description = st.text_area("策略描述", placeholder="简要说明策略逻辑")
            
            st.markdown("**规则配置**")
            template = st.selectbox(
                "选择模板",
                [
                    "自定义",
                    "MA5 金叉 MA20（买入）+ MA5 死叉 MA20（卖出）",
                    "RSI 超卖（<30 买入）+ RSI 超买（>70 卖出）",
                    "MA5 > MA20 且 RSI < 30（买入）",
                ],
            )
            
            submitted = st.form_submit_button("创建策略")
        
        if submitted and name:
            # 根据模板生成规则 JSON
            if template == "自定义":
                rules = {
                    "indicators": [],
                    "conditions": [],
                    "signal_logic": "all",
                    "buy_signal": "conditions_met",
                    "sell_signal": "conditions_not_met",
                }
            elif "MA5 金叉 MA20" in template:
                rules = {
                    "indicators": [
                        {"name": "MA5", "type": "sma", "period": 5, "field": "close"},
                        {"name": "MA20", "type": "sma", "period": 20, "field": "close"},
                    ],
                    "conditions": [
                        {"indicator": "MA5", "operator": ">", "value": "MA20", "value_type": "indicator"},
                    ],
                    "signal_logic": "all",
                    "buy_signal": "conditions_met",
                    "sell_signal": "conditions_not_met",
                }
            elif "RSI 超卖" in template:
                rules = {
                    "indicators": [
                        {"name": "RSI", "type": "rsi", "period": 14, "field": "close"},
                    ],
                    "conditions": [
                        {"indicator": "RSI", "operator": "<", "value": 30, "value_type": "number"},
                    ],
                    "signal_logic": "all",
                    "buy_signal": "conditions_met",
                    "sell_signal": "conditions_not_met",
                }
            elif "MA5 > MA20 且 RSI" in template:
                rules = {
                    "indicators": [
                        {"name": "MA5", "type": "sma", "period": 5, "field": "close"},
                        {"name": "MA20", "type": "sma", "period": 20, "field": "close"},
                        {"name": "RSI", "type": "rsi", "period": 14, "field": "close"},
                    ],
                    "conditions": [
                        {"indicator": "MA5", "operator": ">", "value": "MA20", "value_type": "indicator"},
                        {"indicator": "RSI", "operator": "<", "value": 30, "value_type": "number"},
                    ],
                    "signal_logic": "all",
                    "buy_signal": "conditions_met",
                    "sell_signal": "conditions_not_met",
                }
            else:
                rules = {}
            
            result = _api("POST", "/strategies", json={
                "name": name,
                "description": description or None,
                "rules": rules,
            })
            if result:
                st.success(f"已创建策略: {name}")
                st.rerun()
    
    # 加载策略列表
    strategies = _api("GET", "/strategies") or []
    
    if not strategies:
        st.info("暂无策略，请使用上方表单创建")
        selected_strategy = None
    else:
        for s in strategies:
            cols = st.columns([4, 1])
            label = f"{'✅' if s.get('is_active') else '⏸️'} {s['name']}"
            if cols[0].button(label, key=f"sel_str_{s['id']}", use_container_width=True):
                st.session_state.selected_strategy = s
                st.rerun()
            
            if cols[1].button("🗑️", key=f"del_str_{s['id']}"):
                if _api("DELETE", f"/strategies/{s['id']}"):
                    st.success(f"已删除 {s['name']}")
                    st.rerun()
        
        selected_strategy = st.session_state.get("selected_strategy")

# ════════════════════════════════════════════
# 右侧：回测与结果
# ════════════════════════════════════════════
with right:
    if not selected_strategy:
        st.info("👈 请在左侧选择或创建一个策略")
    else:
        st.markdown(f"### 🎯 {selected_strategy['name']}")
        st.caption(selected_strategy.get("description") or "无描述")
        
        # 显示策略规则
        with st.expander("📜 策略规则"):
            st.json(selected_strategy.get("rules", {}))
        
        st.markdown("---")
        
        # 回测表单
        st.subheader("📊 回测配置")
        with st.form("backtest_form"):
            c1, c2 = st.columns(2)
            stock_code = c1.text_input("股票代码", value="000001.SZ", placeholder="如 000001.SZ")
            c3, c4 = st.columns(2)
            start_date = c3.text_input("开始日期", value="20240101")
            end_date = c4.text_input("结束日期", value="20241231")
            initial_capital = st.number_input("初始资金", value=100000, step=10000)
            run_bt = st.form_submit_button("🚀 执行回测")
        
        if run_bt and stock_code:
            with st.spinner("回测执行中..."):
                result = _api("POST", "/strategies/backtest", json={
                    "strategy_id": selected_strategy["id"],
                    "stock_code": stock_code,
                    "start_date": start_date,
                    "end_date": end_date,
                    "initial_capital": initial_capital,
                })
            
            if result:
                if "error" in result:
                    st.error(f"回测失败: {result['error']}")
                else:
                    # 关键指标卡片
                    st.subheader("📈 回测结果")
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("初始资金", f"¥{result.get('initial_capital', 0):,.0f}")
                    m2.metric("最终资金", f"¥{result.get('final_value', 0):,.2f}")
                    m3.metric("总收益率", result.get("total_return_pct", "N/A"))
                    m4.metric("最大回撤", result.get("max_drawdown_pct", "N/A"))
                    
                    c5, c6 = st.columns(2)
                    c5.metric("交易次数", result.get("trade_count", 0))
                    c6.metric("胜率", result.get("win_rate", "N/A"))
                    
                    st.markdown("---")
                    
                    # 交易记录
                    trades = result.get("trades", [])
                    if trades:
                        with st.expander("📋 交易记录", expanded=True):
                            for t in trades:
                                icon = "🟢" if t["type"] == "buy" else "🔴"
                                st.markdown(f"{icon} **{t['type'].upper()}** | {t['date']} | 价格: {t['price']} | 数量: {t.get('shares', 0):.2f}")
                    
                    # 收益曲线（简单表格展示）
                    equity = result.get("equity_curve", [])
                    if equity:
                        with st.expander("📉 收益曲线数据"):
                            st.dataframe(equity, use_container_width=True)
                    
                    # 实时运行策略（最新信号）
                    st.markdown("---")
                    st.subheader("🔔 最新信号")
                    with st.spinner("获取最新信号..."):
                        signal_result = _api("POST", f"/strategies/{selected_strategy['id']}/run?stock_code={stock_code}&start_date={start_date}&end_date={end_date}")
                    
                    if signal_result and "error" not in signal_result:
                        sig = signal_result.get("signal", "hold")
                        sig_color = {"buy": "🟢", "sell": "🔴", "hold": "⚪"}.get(sig, "⚪")
                        st.markdown(f"### {sig_color} {sig.upper()} | {signal_result.get('signal_date', 'N/A')}")
                        
                        with st.expander("指标数值"):
                            st.json(signal_result.get("indicators", {}))
                    else:
                        st.warning("无法获取最新信号")
