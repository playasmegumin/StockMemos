"""StockMemos 个股详情页"""

import sys
sys.path.append("/app")

from datetime import date, datetime, timezone, timedelta

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


def _api(method: str, path: str, silent: bool = False, **kwargs):
    url = f"{API_BASE}{path}"
    try:
        resp = requests.request(method, url, timeout=30, **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.text:
            return True
        return resp.json()
    except Exception as e:
        if not silent:
            st.error(f"API 请求失败: {e}")
        return None


def _fmt_time(price_time: str | None, default: str = "") -> str:
    """将 UTC ISO 时间转为 UTC+8 时间字符串（YY-MM-DD HH:MM）"""
    if not price_time:
        return default
    try:
        dt = datetime.fromisoformat(price_time.replace("Z", "+00:00"))
        dt_utc8 = dt.astimezone(timezone(timedelta(hours=8)))
        return dt_utc8.strftime("%y-%m-%d %H:%M")
    except Exception:
        return default


# ════════════════════════════════════════════
# Header
# ════════════════════════════════════════════
stock_id = st.session_state.get("current_stock_id")
if not stock_id:
    st.warning("未选择股票，请先返回列表选择。")
    if st.button("← 返回列表"):
        st.switch_page("streamlit_app.py")
    st.stop()

back_col, refresh_col, _ = st.columns([1, 1, 8])
with back_col:
    if st.button("← 返回列表"):
        st.switch_page("streamlit_app.py")
with refresh_col:
    if st.button("🔄 刷新行情", key="refresh_market"):
        with st.spinner("正在刷新行情数据..."):
            result = _api("POST", "/market/refresh")
            if result:
                st.success("行情刷新完成")
                st.rerun()
            else:
                st.error("行情刷新失败")

with st.spinner("正在加载数据..."):
    stock = _api("GET", f"/stocks/{stock_id}")

if stock is None:
    st.error("无法获取股票信息")
    st.stop()

code_str = f"{stock['symbol']}.{stock['exchange']}"
st.title(f"{stock['name']} ({code_str})")

pos = float(stock.get("position", 0))
pnl = float(stock.get("historical_pnl", 0))

# 实时价格 + 浮动盈亏
price_data = st.session_state.get("price_single_cache") if st.session_state.get("data_initialized") else None
if price_data is None:
    price_data = _api("GET", f"/stocks/{stock_id}/price", silent=True)
    if price_data:
        st.session_state["price_single_cache"] = price_data
price_val = float(price_data["price"]) if price_data else None
floating_pnl = price_val * pos + pnl if (price_val and pos) else pnl
price_available = price_val is not None

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("持仓量", f"{pos:,.0f}")
with col2:
    ts = _fmt_time(price_data.get("price_time")) if price_data else ""
    label = f"{price_val:.2f}" if price_available else "当前不可用"
    st.metric("最新价", label)
    if ts:
        st.caption(ts)
with col3:
    st.metric("浮动盈亏", f"{floating_pnl:+.2f}", delta_color="off")
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
# Fundamentals — 只读展示（后台自动拉取）
# ════════════════════════════════════════════
st.subheader("📊 基本面数据")

# 如无基本面数据且未初始化，自动触发刷新
fundamentals = analyze.get("fundamentals_data") or {}
if not fundamentals and not st.session_state.get("data_initialized"):
    with st.spinner("正在拉取基本面数据..."):
        result = _api("POST", "/market/refresh-fundamentals", silent=True)
        if result:
            st.session_state["data_initialized"] = True
            st.rerun()

fundamentals = analyze.get("fundamentals_data") or {}

if fundamentals.get("source"):
    source_name = "yfinance" if fundamentals["source"] == "yfinance" else "TuShare" if fundamentals["source"] == "tushare" else fundamentals["source"]
    data_date = fundamentals.get("data_date", "")
    st.caption(f"来源: {source_name}　|　更新日: {data_date}")

FUND_FIELDS = [
    ("pe_ratio", "PE（市盈率）"),
    ("pb_ratio", "PB（市净率）"),
    ("market_cap", "总市值"),
    ("roe", "ROE"),
    ("dividend_yield", "股息率"),
    ("eps", "每股收益"),
    ("profit_margin", "净利率"),
    ("debt_to_equity", "资产负债率"),
]

with st.container(border=True):
    cols_row = st.columns(2)
    for idx, (key, label) in enumerate(FUND_FIELDS):
        val = fundamentals.get(key)
        with cols_row[idx % 2]:
            if val is not None:
                display = f"{float(val):,.2f}" if isinstance(val, (int, float)) else str(val)
                st.markdown(f"**{label}**  \n{display}")
            else:
                st.markdown(f"**{label}**  \n—")

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
