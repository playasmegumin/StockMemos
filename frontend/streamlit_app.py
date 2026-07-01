"""StockMemos 主入口 — 首页 = 持仓总览

设置页面全局配置、侧边栏导航，以及持仓总览 Dashboard。
"""

import sys
sys.path.append("/app")
from app.components.sidebar import render_sidebar


import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="持仓总览",
    page_icon="📈",
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


# ── 侧边栏 ─────────────────────────────
st.sidebar.markdown("""
    <style>
    /* 隐藏默认页面导航 */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title("📊 StockMemos")

# 自定义页面导航
st.sidebar.page_link("streamlit_app.py", label="📈 持仓总览")

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

# ── 配置 ──────────────────────────────────
API_BASE = "http://backend:8080/api"


def _api(method: str, path: str, **kwargs):
    """统一 API 调用

    特殊处理：
    - 204 No Content → 返回 True（无响应体）
    - 空响应 → 返回 True
    """
    url = f"{API_BASE}{path}"
    try:
        resp = requests.request(method, url, timeout=30, **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.text:
            return True
        return resp.json()
    except Exception as e:
        st.error(f"API 请求失败: {e}")
        return None


# ════════════════════════════════════════════
# 持仓总览 Dashboard
# ════════════════════════════════════════════
st.title("📈 持仓总览")
st.caption("实时盈亏跟踪 · 仓位管理 Dashboard")

# 加载数据
with st.spinner("正在拉取最新行情..."):
    data = _api("GET", "/portfolio/dashboard")

if not data:
    st.warning("暂无持仓数据，请先在下方添加持仓。")
    positions = []
    summary = {
        "total_cost": 0.0,
        "total_market_value": 0.0,
        "total_floating_pnl": 0.0,
        "total_pnl_rate": 0.0,
        "position_count": 0,
    }
else:
    positions = data.get("positions", [])
    summary = data.get("summary", {})

# ── 顶部汇总卡片 ──────────────────────────
st.markdown("---")

cols = st.columns(5)
cols[0].metric(
    label="💰 总市值",
    value=f"¥{summary.get('total_market_value', 0):,.2f}",
    delta=f"¥{summary.get('total_floating_pnl', 0):,.2f}",
)
cols[1].metric(
    label="📥 总成本",
    value=f"¥{summary.get('total_cost', 0):,.2f}",
)
cols[2].metric(
    label="📈 浮动盈亏",
    value=f"¥{summary.get('total_floating_pnl', 0):,.2f}",
    delta=f"{summary.get('total_pnl_rate', 0)*100:.2f}%",
    delta_color="normal",
)
cols[3].metric(
    label="📊 总收益率",
    value=f"{summary.get('total_pnl_rate', 0)*100:.2f}%",
)
cols[4].metric(
    label="🏷️ 持仓数量",
    value=f"{summary.get('position_count', 0)} 只",
)

st.markdown("---")

# ── 持仓明细表格 ──────────────────────────
st.subheader("📋 持仓明细")

if positions:
    df = pd.DataFrame(positions)
    df_display = df.rename(columns={
        "stock_code": "代码",
        "stock_name": "名称",
        "quantity": "数量",
        "cost_price": "成本价",
        "latest_price": "最新价",
        "market_value": "市值",
        "floating_pnl": "浮动盈亏",
        "pnl_rate": "盈亏率",
        "status": "状态",
    })
    df_display["盈亏率"] = df_display["盈亏率"].apply(lambda x: f"{x*100:.2f}%")
    df_display["成本价"] = df_display["成本价"].apply(lambda x: f"{x:.2f}")
    df_display["最新价"] = df_display["最新价"].apply(lambda x: f"{x:.2f}")
    df_display["市值"] = df_display["市值"].apply(lambda x: f"{x:,.2f}")
    df_display["浮动盈亏"] = df_display["浮动盈亏"].apply(lambda x: f"{x:+,.2f}")

    st.dataframe(
        df_display[["代码", "名称", "数量", "成本价", "最新价", "市值", "浮动盈亏", "盈亏率"]],
        use_container_width=True,
        hide_index=True,
    )

    # 快捷操作
    st.subheader("⚡ 快捷操作")
    for i, pos in enumerate(positions):
        cols = st.columns([3, 2, 2, 2, 2])
        cols[0].markdown(f"**{pos['stock_code']}** {pos.get('stock_name', '')}")

        if cols[1].button("🔍 分析", key=f"analyze_{pos['id']}"):
            st.session_state.analyze_stock_code = pos['stock_code']
            st.switch_page("pages/2_个股分析.py")

        if cols[2].button("➕ 加仓", key=f"add_{pos['id']}"):
            st.session_state.add_position_id = pos['id']

        if cols[3].button("➖ 减仓", key=f"reduce_{pos['id']}"):
            st.session_state.reduce_position_id = pos['id']

        if cols[4].button("🗑️ 删除", key=f"del_{pos['id']}"):
            if _api("DELETE", f"/portfolio/{pos['id']}"):
                st.success(f"已删除 {pos['stock_code']}")
                st.rerun()
            else:
                st.error("删除失败")

    # ── 加仓/减仓表单 ─────────────────────────
    # 加仓
    add_id = st.session_state.get("add_position_id")
    if add_id:
        pos = next((p for p in positions if p['id'] == add_id), None)
        if pos:
            with st.container(border=True):
                st.markdown(f"**➕ 加仓 {pos['stock_code']}**")
                c1, c2 = st.columns(2)
                add_qty = c1.number_input("加仓数量", min_value=1, value=100, step=100, key="add_qty")
                add_price = c2.number_input("加仓价格", min_value=0.01, value=pos['latest_price'] or pos['cost_price'], step=0.01, format="%.2f", key="add_price")
                c3, c4 = st.columns(2)
                if c3.button("✅ 确认加仓", key="confirm_add"):
                    # 新成本价 = (原成本×原数量 + 加仓价格×加仓数量) / 总数量
                    total_qty = pos['quantity'] + add_qty
                    new_cost = (pos['cost_price'] * pos['quantity'] + add_price * add_qty) / total_qty
                    result = _api("PUT", f"/portfolio/{pos['id']}", json={
                        "stock_code": pos['stock_code'],
                        "stock_name": pos.get('stock_name'),
                        "quantity": total_qty,
                        "cost_price": new_cost,
                        "build_date": pos['build_date'],
                        "status": "holding",
                    })
                    if result:
                        st.success(f"✅ 已加仓 {add_qty} 股，新成本价 ¥{new_cost:.2f}")
                        del st.session_state["add_position_id"]
                        st.rerun()
                if c4.button("❌ 取消", key="cancel_add"):
                    del st.session_state["add_position_id"]
                    st.rerun()

    # 减仓
    reduce_id = st.session_state.get("reduce_position_id")
    if reduce_id:
        pos = next((p for p in positions if p['id'] == reduce_id), None)
        if pos:
            with st.container(border=True):
                st.markdown(f"**➖ 减仓 {pos['stock_code']}**")
                reduce_qty = st.number_input("减仓数量", min_value=1, max_value=pos['quantity'], value=min(100, pos['quantity']), step=100, key="reduce_qty")
                c1, c2 = st.columns(2)
                if c1.button("✅ 确认减仓", key="confirm_reduce"):
                    remaining = pos['quantity'] - reduce_qty
                    if remaining <= 0:
                        # 清仓
                        if _api("DELETE", f"/portfolio/{pos['id']}"):
                            st.success(f"✅ 已清仓 {pos['stock_code']}")
                            del st.session_state["reduce_position_id"]
                            st.rerun()
                    else:
                        # 部分减仓，成本价不变
                        result = _api("PUT", f"/portfolio/{pos['id']}", json={
                            "stock_code": pos['stock_code'],
                            "stock_name": pos.get('stock_name'),
                            "quantity": remaining,
                            "cost_price": pos['cost_price'],
                            "build_date": pos['build_date'],
                            "status": "holding",
                        })
                        if result:
                            st.success(f"✅ 已减仓 {reduce_qty} 股，剩余 {remaining} 股")
                            del st.session_state["reduce_position_id"]
                            st.rerun()
                if c2.button("❌ 取消", key="cancel_reduce"):
                    del st.session_state["reduce_position_id"]
                    st.rerun()

else:
    st.info("暂无持仓记录，请使用下方表单添加。")

st.markdown("---")

# ── 新增持仓 ──────────────────────────────
with st.expander("➕ 新增持仓", expanded=not positions):
    with st.form("new_portfolio"):
        c1, c2 = st.columns(2)
        stock_code = c1.text_input("股票代码", placeholder="如 000001.SZ")
        stock_name = c2.text_input("股票名称", placeholder="如 平安银行")

        c3, c4 = st.columns(2)
        quantity = c3.number_input("持股数量", min_value=1, value=100, step=100)
        cost_price = c4.number_input("成本价", min_value=0.01, value=10.0, step=0.01, format="%.2f")

        build_date = st.date_input("建仓日期", value=datetime.today())
        submitted = st.form_submit_button("📝 保存持仓", use_container_width=True)

    if submitted:
        payload = {
            "stock_code": stock_code,
            "stock_name": stock_name or None,
            "quantity": int(quantity),
            "cost_price": float(cost_price),
            "build_date": build_date.strftime("%Y-%m-%d"),
            "status": "holding",
        }
        result = _api("POST", "/portfolio", json=payload)
        if result:
            st.success(f"✅ 已添加 {stock_code} {stock_name}")
            st.rerun()

# ── 板块概览 ────────────────────────────
if positions:
    st.markdown("---")
    st.subheader("🧩 板块概览")
    st.caption("按股票名称简单分组（后续可按行业分类）")

    fig = px.pie(
        df,
        values="market_value",
        names="stock_name",
        title="持仓市值分布",
        hole=0.4,
    )
    fig.update_layout(showlegend=True, height=400)
    st.plotly_chart(fig, use_container_width=True)
