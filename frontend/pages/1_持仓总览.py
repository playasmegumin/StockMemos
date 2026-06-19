"""持仓总览页 — 参考 ace-portfolio 的排版风格

核心布局：
    1. 顶部汇总卡片（总市值 · 总成本 · 浮动盈亏 · 收益率 · 持仓数）
    2. 板块概览（饼图/进度条）
    3. 持仓明细表格（含操作按钮：分析/加仓/减仓/删除）
    4. 新增持仓表单（折叠面板）
"""

import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# ── 全局 CSS：页面宽度完全铺满（每个页面独立注入）──
st.markdown("""
    <style>
    .stApp .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    [data-testid="stSidebar"] {
        width: 16rem !important;
        min-width: 16rem !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    .stDataFrame td {
        white-space: nowrap !important;
    }
    </style>
""", unsafe_allow_html=True)

# ── 配置 ───────────────────────────────
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
        # 处理 204 No Content 或其他空响应
        if resp.status_code == 204 or not resp.text:
            return True
        return resp.json()
    except Exception as e:
        st.error(f"API 请求失败: {e}")
        return None

# ── 页面标题 ───────────────────────────────
st.title("📈 持仓总览")
st.caption("实时盈亏跟踪 · 仓位管理 Dashboard")

# ── 加载 Dashboard 数据 ─────────────────────
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

# ════════════════════════════════════════════
# 1. 顶部汇总卡片
# ════════════════════════════════════════════
st.markdown("---")

cols = st.columns(5)

# 卡片 1: 总市值
cols[0].metric(
    label="💰 总市值",
    value=f"¥{summary.get('total_market_value', 0):,.2f}",
    delta=f"¥{summary.get('total_floating_pnl', 0):,.2f}",
)

# 卡片 2: 总成本
cols[1].metric(
    label="📥 总成本",
    value=f"¥{summary.get('total_cost', 0):,.2f}",
)

# 卡片 3: 浮动盈亏
cols[2].metric(
    label="📈 浮动盈亏",
    value=f"¥{summary.get('total_floating_pnl', 0):,.2f}",
    delta=f"{summary.get('total_pnl_rate', 0)*100:.2f}%",
    delta_color="normal",
)

# 卡片 4: 总收益率
cols[3].metric(
    label="📊 总收益率",
    value=f"{summary.get('total_pnl_rate', 0)*100:.2f}%",
)

# 卡片 5: 持仓数量
cols[4].metric(
    label="🏷️ 持仓数量",
    value=f"{summary.get('position_count', 0)} 只",
)

st.markdown("---")

# ════════════════════════════════════════════
# 2. 持仓明细表格（核心）
# ════════════════════════════════════════════
st.subheader("📋 持仓明细")

if positions:
    df = pd.DataFrame(positions)
    # 重命名列，便于展示
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

    # 操作按钮区
    st.subheader("⚡ 快捷操作")
    for i, pos in enumerate(positions):
        cols = st.columns([3, 2, 2, 2, 2])
        cols[0].markdown(f"**{pos['stock_code']}** {pos.get('stock_name', '')}")

        if cols[1].button("🔍 分析", key=f"analyze_{pos['id']}"):
            st.switch_page("pages/2_个股分析.py")

        if cols[2].button("➕ 加仓", key=f"add_{pos['id']}"):
            st.info(f"加仓 {pos['stock_code']} — 功能开发中")

        if cols[3].button("➖ 减仓", key=f"reduce_{pos['id']}"):
            st.info(f"减仓 {pos['stock_code']} — 功能开发中")

        if cols[4].button("🗑️ 删除", key=f"del_{pos['id']}"):
            if _api("DELETE", f"/portfolio/{pos['id']}"):
                st.success(f"已删除 {pos['stock_code']}")
                st.rerun()
            else:
                st.error("删除失败")

else:
    st.info("暂无持仓记录，请使用下方表单添加。")

st.markdown("---")

# ════════════════════════════════════════════
# 3. 新增持仓表单
# ════════════════════════════════════════════
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

# ════════════════════════════════════════════
# 4. 板块概览（简单饼图）
# ════════════════════════════════════════════
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
