"""StockMemos 个股详情页"""

import sys
sys.path.append("/app")

from datetime import date, datetime, timezone

import requests
import streamlit as st
from app.components.sidebar import render_sidebar

st.set_page_config(page_title="个股详情", layout="wide")

st.markdown("""
    <style>
    .stApp .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    .tag-pill {
        display: inline-block; background: #eef2ff; color: #4f46e5;
        border-radius: 12px; padding: 2px 10px; font-size: 0.8rem;
        margin: 2px 4px; white-space: nowrap;
    }
    .tag-pill .del { margin-left: 4px; cursor: pointer; color: #999; }
    .tag-pill .del:hover { color: #dc2626; }
    .inline-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
    .buy-row { background-color: #fff5f5; }
    .sell-row { background-color: #f0fff4; }
    .fund-annotation { font-size: 0.75rem; color: #888; margin-top: -8px; margin-bottom: 8px; }
    [data-testid="stSidebarNavItems"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

render_sidebar()

API_BASE = "http://backend:8080/api"


def _api(method: str, path: str, **kwargs):
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
# Header
# ════════════════════════════════════════════
stock_id = st.session_state.get("current_stock_id")
if not stock_id:
    st.warning("未选择股票，请先返回列表选择。")
    if st.button("← 返回列表"):
        st.switch_page("streamlit_app.py")
    st.stop()

back_col, _ = st.columns([1, 10])
with back_col:
    if st.button("← 返回列表"):
        st.switch_page("streamlit_app.py")

with st.spinner("正在加载数据..."):
    stock = _api("GET", f"/stocks/{stock_id}")

if stock is None:
    st.error("无法获取股票信息")
    st.stop()

code_str = f"{stock['exchange']}.{stock['symbol']}"
st.title(f"{stock['name']} ({code_str})")

col1, col2, col3, col4 = st.columns(4)
pnl = float(stock.get("historical_pnl", 0))
with col1:
    st.metric("持仓量", f"{float(stock.get('position', 0)):,.0f}")
with col2:
    st.metric("历史盈亏", f"{pnl:+.2f}", delta_color="off")
with col3:
    st.metric("交易所", stock["exchange"])
with col4:
    st.metric("货币", stock["currency"])

# ── 获取分析 ID（自动创建）─────────────────
analyze = _api("GET", f"/stock-analyze/stock/{stock_id}")
if not analyze or not analyze.get("id"):
    st.error("无法获取或创建分析记录")
    st.stop()
analyze_id = analyze["id"]

# ════════════════════════════════════════════
# Tags — 作为基本情况的属性行
# ════════════════════════════════════════════
tags = _api("GET", f"/stock-analyze/{analyze_id}/stock-tags") or []

tag_items = [t["tag"] for t in tags]
tag_cols = st.columns([1] + [1] * len(tags) + [2])

with tag_cols[0]:
    st.markdown("**标签：**")

if tags:
    for i, t in enumerate(tags):
        with tag_cols[i + 1]:
            if st.button(f"{t['tag']} ×", key=f"del_tag_{t['id']}",
                         help="删除标签", use_container_width=True):
                if _api("DELETE", f"/stock-analyze/{analyze_id}/stock-tags/{t['id']}"):
                    st.rerun()
else:
    with tag_cols[1]:
        st.caption("暂无")

# 内联添加标签
add_tag_cols = st.columns([2, 1])
with add_tag_cols[0]:
    new_tag = st.text_input("新标签", label_visibility="collapsed",
                            placeholder="输入标签...", key="tag_input")
with add_tag_cols[1]:
    if st.button("+ 添加", key="add_tag_btn", use_container_width=True):
        if new_tag.strip():
            if _api("POST", f"/stock-analyze/{analyze_id}/stock-tags",
                    json={"tag": new_tag.strip()}):
                st.rerun()

st.divider()

# ════════════════════════════════════════════
# Fundamentals — 结构化表单 + 注解
# ════════════════════════════════════════════
st.subheader("📊 基本面数据")

fundamentals = analyze.get("fundamentals_data") or {}

FUND_FIELDS = [
    ("pe_ttm", "PE_TTM（滚动市盈率）", "总市值 / 最近12个月净利润"),
    ("pb", "PB（市净率）", "总市值 / 净资产"),
    ("roe", "ROE（净资产收益率 %）", "净利润 / 净资产 × 100%"),
    ("market_cap", "总市值", "总股本 × 当前股价"),
    ("dividend_yield", "股息率（%）", "每股分红 / 每股股价 × 100%"),
    ("profit_growth_rate", "营收增长率（%）", "（本期营收 - 上期营收）/ 上期营收 × 100%"),
    ("net_profit_margin", "净利率（%）", "净利润 / 营业收入 × 100%"),
    ("debt_ratio", "资产负债率（%）", "总负债 / 总资产 × 100%"),
]

with st.container(border=True):
    fund_form = {}
    cols_row = st.columns(2)
    for idx, (key, label, annotation) in enumerate(FUND_FIELDS):
        with cols_row[idx % 2]:
            current_val = fundamentals.get(key)
            if current_val is not None:
                fund_form[key] = st.number_input(
                    label, value=float(current_val),
                    format="%.4f" if any(k in key for k in ["roe", "yield", "margin", "ratio", "growth"]) else "%.2f",
                    key=f"fund_{key}"
                )
            else:
                fund_form[key] = st.number_input(
                    label, value=0.0, format="%.4f",
                    key=f"fund_{key}"
                )
            st.markdown(f'<div class="fund-annotation">{annotation}</div>',
                        unsafe_allow_html=True)

    if st.button("保存基本面数据", use_container_width=True):
        updated = {k: v for k, v in fund_form.items()}
        if _api("PUT", f"/stock-analyze/{analyze_id}",
                json={"fundamentals_data": updated}):
            st.success("基本面数据已更新")
            st.rerun()

st.divider()

# ════════════════════════════════════════════
# TP/SL Points — 内联添加行
# ════════════════════════════════════════════
st.subheader("🎯 止盈止损点")

tp_sl_points = _api("GET", f"/stock-analyze/{analyze_id}/tp-sl-points") or []

if tp_sl_points:
    for pt in tp_sl_points:
        cols = st.columns([2, 2, 3, 1])
        with cols[0]:
            st.markdown(f"**{pt['label']}**")
        with cols[1]:
            st.markdown(f"{float(pt['price']):.2f}")
        with cols[2]:
            st.markdown(f"{pt.get('notes') or '—'}")
        with cols[3]:
            if st.button("🗑️", key=f"del_tp_{pt['id']}"):
                if _api("DELETE", f"/stock-analyze/{analyze_id}/tp-sl-points/{pt['id']}"):
                    st.rerun()

# 内联添加行
st.markdown("**添加条目：**")
add_cols = st.columns([1.5, 1.5, 3, 1])
with add_cols[0]:
    tp_label = st.selectbox("类型", options=["止盈", "止损", "其他"],
                            key="tp_label")
with add_cols[1]:
    tp_price = st.number_input("数值", min_value=0.01, step=0.01, format="%.2f",
                               key="tp_price")
with add_cols[2]:
    tp_notes = st.text_input("备注", placeholder="备注（可选）",
                             key="tp_notes")
with add_cols[3]:
    if st.button("+ 添加", key="add_tp_btn", use_container_width=True):
        if tp_price > 0:
            if _api("POST", f"/stock-analyze/{analyze_id}/tp-sl-points", json={
                "price": tp_price, "label": tp_label, "notes": tp_notes.strip() or None,
            }):
                st.rerun()

st.divider()

# ════════════════════════════════════════════
# Transactions — 内联添加行
# ════════════════════════════════════════════
st.subheader("💰 交易记录")

transactions = _api("GET", f"/transactions/stock/{stock_id}") or []

# 内联添加行
exchange = stock.get("exchange", "")
default_gas = 5.0 if exchange in ("CN", "SH", "SZ") else 18.0 if exchange == "HK" else 1.99 if exchange == "US" else 0.0

st.markdown("**添加条目：**")
add_row = st.columns([1.2, 1.5, 1.5, 1.5, 2, 0.8])
with add_row[0]:
    txn_type = st.selectbox("类型", options=["买入", "卖出"],
                            key="txn_type")
with add_row[1]:
    price = st.number_input("价格", min_value=0.01, step=1.0, format="%.2f",
                            key="txn_price")
with add_row[2]:
    qty = st.number_input("数量", min_value=0.01, step=100.0, format="%.2f",
                          key="txn_qty")
with add_row[3]:
    gas = st.number_input("手续费", min_value=0.0, step=1.0, format="%.2f",
                          value=default_gas, key="txn_gas")
with add_row[4]:
    traded_at = st.date_input("交易日期", value=date.today(),
                              key="txn_date")
with add_row[5]:
    if st.button("+ 添加", key="add_txn_btn", use_container_width=True):
        quantity_val = qty if txn_type == "买入" else -qty
        if _api("POST", "/transactions", json={
            "stock_id": stock_id, "quantity": quantity_val, "price": price,
            "gas": gas, "traded_at": str(traded_at),
        }):
            st.rerun()

# Transaction table
if transactions:
    st.markdown("---")
    # Header row
    hcols = st.columns([1, 1.5, 1.5, 1.5, 2, 1, 1])
    headers = ["类型", "价格", "数量", "手续费", "交易日期", "", ""]
    for ci, h in enumerate(headers):
        with hcols[ci]:
            st.markdown(f"**{h}**" if h else "")

    for txn in transactions:
        is_buy = txn["quantity"] > 0
        txn_label = "买入" if is_buy else "卖出"
        qty_display = abs(txn["quantity"])
        row_class = "buy-row" if is_buy else "sell-row"

        cols = st.columns([1, 1.5, 1.5, 1.5, 2, 1, 1])
        with cols[0]:
            st.markdown(f"<span style='background:{'#fee2e2' if is_buy else '#dcfce7'};padding:2px 8px;border-radius:4px;'>{txn_label}</span>",
                        unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"{txn['price']:.2f}")
        with cols[2]:
            st.markdown(f"{qty_display:,.2f}")
        with cols[3]:
            st.markdown(f"{txn['gas']:.2f}")
        with cols[4]:
            st.markdown(str(txn.get("traded_at", "")))
        with cols[5]:
            edit_key = f"edit_{txn['id']}"
            st.button("✏️", key=edit_key)
        with cols[6]:
            if st.button("🗑️", key=f"del_{txn['id']}"):
                if _api("DELETE", f"/transactions/{txn['id']}"):
                    st.rerun()

        # Inline edit (only shown when edit button clicked)
        if st.session_state.get(edit_key, False):
            with st.container(border=True):
                st.caption(f"编辑交易")
                ef_cols = st.columns([1.2, 1.2, 1.2, 1, 1.5])
                with ef_cols[0]:
                    e_type = st.selectbox("类型", options=["买入", "卖出"],
                                          index=0 if is_buy else 1,
                                          key=f"et_{txn['id']}")
                with ef_cols[1]:
                    e_price = st.number_input("价格", value=txn["price"], min_value=0.01,
                                              format="%.2f", key=f"ep_{txn['id']}")
                with ef_cols[2]:
                    e_qty = st.number_input("数量", value=qty_display, min_value=0.01,
                                            format="%.2f", key=f"eq_{txn['id']}")
                with ef_cols[3]:
                    e_gas = st.number_input("手续费", value=txn["gas"], min_value=0.0,
                                            format="%.2f", key=f"eg_{txn['id']}")
                with ef_cols[4]:
                    try:
                        e_date = date.fromisoformat(str(txn["traded_at"]))
                    except (ValueError, TypeError):
                        e_date = date.today()
                    e_traded = st.date_input("日期", value=e_date, key=f"ed_{txn['id']}")

                if st.button("保存修改", key=f"save_{txn['id']}"):
                    e_qty_val = e_qty if e_type == "买入" else -e_qty
                    if _api("PUT", f"/transactions/{txn['id']}", json={
                        "quantity": e_qty_val, "price": e_price, "gas": e_gas,
                        "traded_at": str(e_traded),
                    }):
                        st.session_state[edit_key] = False
                        st.rerun()
                st.button("取消", key=f"cancel_{txn['id']}",
                          on_click=lambda k=edit_key: st.session_state.update({k: False}))
else:
    st.caption("暂无交易记录")

st.divider()

# ════════════════════════════════════════════
# Reports — 标签页
# ════════════════════════════════════════════
st.subheader("📄 分析报告")

reports = _api("GET", f"/stock-analyze/{analyze_id}/reports") or []

if reports:
    tab_titles = [r.get("title", f"报告 {i+1}") for i, r in enumerate(reports)]
    tabs = st.tabs(tab_titles)
    for i, tab in enumerate(tabs):
        with tab:
            r = reports[i]
            st.caption(f"生成时间: {r.get('generated_at', '—')}")
            st.markdown(r.get("content", ""))
else:
    st.caption("暂无分析报告")

with st.expander("➕ 添加分析报告", expanded=False):
    with st.form("add_report_form"):
        report_title = st.text_input("报告标题", placeholder="输入报告标题...")
        report_content = st.text_area("报告内容", height=200, placeholder="输入报告正文...")
        if st.form_submit_button("添加"):
            if report_title.strip() and report_content.strip():
                if _api("POST", f"/stock-analyze/{analyze_id}/reports", json={
                    "title": report_title.strip(),
                    "content": report_content.strip(),
                    "generated_at": datetime.now().isoformat(),
                }):
                    st.rerun()
            else:
                st.error("标题和内容不能为空")
