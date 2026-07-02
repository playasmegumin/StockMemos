"""StockMemos 个股详情页"""

import sys
sys.path.append("/app")

import json
from datetime import date, datetime

import requests
import streamlit as st
from app.components.sidebar import render_sidebar

st.set_page_config(page_title="个股详情", layout="wide")

# ── CSS ─────────────────────────────
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
    .tag-pill .delete-btn {
        display: inline-block; margin-left: 4px; cursor: pointer;
        color: #4f46e5; font-weight: bold;
    }
    .tag-pill .delete-btn:hover { color: #dc2626; }
    .buy-row { background-color: #fff5f5 !important; }
    .sell-row { background-color: #f0fff4 !important; }
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
pnl_style = "positive" if pnl >= 0 else "negative"
with col1:
    st.metric("持仓量", f"{float(stock.get('position', 0)):,.0f}")
with col2:
    st.metric("历史盈亏", f"{pnl:+.2f}", delta_color="off")
with col3:
    st.metric("交易所", stock["exchange"])
with col4:
    st.metric("货币", stock["currency"])

st.divider()

# ── 获取分析 ID（自动创建）─────────────────
analyze = _api("GET", f"/stock-analyze/stock/{stock_id}")
if not analyze or not analyze.get("id"):
    st.error("无法获取或创建分析记录")
    st.stop()
analyze_id = analyze["id"]

# ════════════════════════════════════════════
# Block 2: Tags
# ════════════════════════════════════════════
st.subheader("🏷️ 标签")

tags = _api("GET", f"/stock-analyze/{analyze_id}/stock-tags") or []

if tags:
    tag_cols = st.columns([1] * len(tags))
    for i, t in enumerate(tags):
        with tag_cols[i]:
            pill_html = f'<span class="tag-pill">{t["tag"]}</span>'
            st.markdown(pill_html, unsafe_allow_html=True)
            if st.button("×", key=f"del_tag_{t['id']}", help="删除标签"):
                if _api("DELETE", f"/stock-analyze/{analyze_id}/stock-tags/{t['id']}"):
                    st.rerun()
else:
    st.caption("暂无标签")

# Add tag
col_tag_input, col_tag_btn = st.columns([3, 1])
with col_tag_input:
    new_tag = st.text_input("新标签", label_visibility="collapsed", placeholder="输入新标签...", key="tag_input")
with col_tag_btn:
    if st.button("添加", use_container_width=True):
        if new_tag.strip():
            if _api("POST", f"/stock-analyze/{analyze_id}/stock-tags", json={"tag": new_tag.strip()}):
                st.rerun()
        else:
            st.error("标签不能为空")

st.divider()

# ════════════════════════════════════════════
# Block 3: Fundamentals
# ════════════════════════════════════════════
st.subheader("📊 基本面数据")

fundamentals = analyze.get("fundamentals_data")

if fundamentals:
    # Display as key-value table
    f_data = []
    for k, v in fundamentals.items():
        if isinstance(v, (int, float)):
            f_data.append({"指标": k, "值": f"{v:,.2f}" if isinstance(v, float) else str(v)})
        else:
            f_data.append({"指标": k, "值": str(v)})
    st.table(f_data)

    # Edit toggle
    if "show_fund_edit" not in st.session_state:
        st.session_state.show_fund_edit = False

    if st.button("编辑基本面数据", key="toggle_fund_edit"):
        st.session_state.show_fund_edit = not st.session_state.show_fund_edit

    if st.session_state.show_fund_edit:
        with st.container(border=True):
            fund_json = json.dumps(fundamentals, ensure_ascii=False, indent=2)
            new_fund = st.text_area("基本面数据 (JSON)", value=fund_json, height=200, key="fund_edit_area")
            if st.button("保存基本面数据"):
                try:
                    parsed = json.loads(new_fund)
                    result = _api("PUT", f"/stock-analyze/{analyze_id}", json={"fundamentals_data": parsed})
                    if result:
                        st.success("基本面数据已更新")
                        st.session_state.show_fund_edit = False
                        st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"JSON 格式错误: {e}")
else:
    st.caption("暂无基本面数据")
    if st.button("添加基本面数据", key="toggle_fund_add"):
        st.session_state.show_fund_edit = True

    if st.session_state.get("show_fund_edit"):
        with st.container(border=True):
            fund_json = st.text_area(
                "基本面数据 (JSON)", value="{}", height=200,
                key="fund_add_area"
            )
            if st.button("保存基本面数据"):
                try:
                    parsed = json.loads(fund_json)
                    result = _api("PUT", f"/stock-analyze/{analyze_id}", json={"fundamentals_data": parsed})
                    if result:
                        st.success("基本面数据已保存")
                        st.session_state.show_fund_edit = False
                        st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"JSON 格式错误: {e}")

st.divider()

# ════════════════════════════════════════════
# Block 4: TP/SL Points
# ════════════════════════════════════════════
st.subheader("🎯 止盈止损点")

tp_sl_points = _api("GET", f"/stock-analyze/{analyze_id}/tp-sl-points") or []

if tp_sl_points:
    for pt in tp_sl_points:
        cols = st.columns([2, 2, 3, 1])
        with cols[0]:
            st.markdown(f"**{pt['label']}**")
        with cols[1]:
            st.markdown(f"价格: {pt['price']:.2f}")
        with cols[2]:
            notes = pt.get("notes")
            st.markdown(f"{notes or '—'}")
        with cols[3]:
            if st.button("🗑️", key=f"del_tp_{pt['id']}"):
                if _api("DELETE", f"/stock-analyze/{analyze_id}/tp-sl-points/{pt['id']}"):
                    st.rerun()
else:
    st.caption("暂无止盈止损点")

with st.expander("➕ 添加止盈止损点", expanded=False):
    with st.form("tp_sl_form"):
        tp_price = st.number_input("价格", min_value=0.01, step=0.01, format="%.2f")
        tp_label = st.selectbox("类型", options=["买入", "卖出", "目标估值"])
        tp_notes = st.text_input("备注（可选）")
        if st.form_submit_button("添加"):
            if _api("POST", f"/stock-analyze/{analyze_id}/tp-sl-points", json={
                "price": tp_price,
                "label": tp_label,
                "notes": tp_notes.strip() or None,
            }):
                st.rerun()

st.divider()

# ════════════════════════════════════════════
# Block 5: Transactions
# ════════════════════════════════════════════
st.subheader("💰 交易记录")

transactions = _api("GET", f"/transactions/stock/{stock_id}") or []

# Add transaction form
with st.expander("➕ 添加交易记录", expanded=False):
    with st.form("add_txn_form"):
        txn_type = st.radio("类型", options=["买入", "卖出"], horizontal=True)
        row = st.columns(4)
        with row[0]:
            qty = st.number_input("数量", min_value=0.01, step=100.0, format="%.2f")
        with row[1]:
            price = st.number_input("价格", min_value=0.01, step=1.0, format="%.2f")
        with row[2]:
            # Gas default based on exchange
            exchange = stock.get("exchange", "")
            if exchange in ("CN", "SH", "SZ"):
                default_gas = 5.0
            elif exchange == "HK":
                default_gas = 18.0
            elif exchange == "US":
                default_gas = 1.99
            else:
                default_gas = 0.0
            gas = st.number_input("手续费", min_value=0.0, step=1.0, format="%.2f", value=default_gas)
        with row[3]:
            traded_at = st.date_input("交易日期", value=date.today())

        if st.form_submit_button("添加"):
            quantity_val = qty if txn_type == "买入" else -qty
            if _api("POST", "/transactions", json={
                "stock_id": stock_id,
                "quantity": quantity_val,
                "price": price,
                "gas": gas,
                "traded_at": str(traded_at),
            }):
                st.success("交易记录已添加")
                st.rerun()

# Transaction table
if transactions:
    # Prepare table data
    for txn in transactions:
        is_buy = txn["quantity"] > 0
        row_class = "buy-row" if is_buy else "sell-row"
        txn_type_label = "买入" if is_buy else "卖出"
        qty_display = abs(txn["quantity"])

        cols = st.columns([1, 1.5, 1.5, 1.5, 2, 1, 1])
        with cols[0]:
            st.markdown(f"<span class='{row_class}' style='padding:2px 8px;border-radius:4px;'>{txn_type_label}</span>",
                        unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"{qty_display:,.2f}")
        with cols[2]:
            st.markdown(f"{txn['price']:.2f}")
        with cols[3]:
            st.markdown(f"{txn['gas']:.2f}")
        with cols[4]:
            st.markdown(str(txn.get("traded_at", "")))
        with cols[5]:
            # Edit button toggles inline form
            edit_key = f"edit_txn_{txn['id']}"
            if st.button("✏️", key=edit_key):
                st.session_state[f"editing_txn_{txn['id']}"] = not st.session_state.get(f"editing_txn_{txn['id']}", False)
        with cols[6]:
            if st.button("🗑️", key=f"del_txn_{txn['id']}"):
                if _api("DELETE", f"/transactions/{txn['id']}"):
                    st.rerun()

        # Inline edit form
        if st.session_state.get(f"editing_txn_{txn['id']}", False):
            with st.container(border=True):
                st.caption(f"编辑交易记录 ({txn_type_label})")
                with st.form(f"edit_txn_form_{txn['id']}"):
                    edit_row = st.columns(4)
                    with edit_row[0]:
                        e_qty = st.number_input("数量", value=abs(txn["quantity"]),
                                                min_value=0.01, step=100.0, format="%.2f",
                                                key=f"eqty_{txn['id']}")
                    with edit_row[1]:
                        e_price = st.number_input("价格", value=txn["price"],
                                                  min_value=0.01, step=1.0, format="%.2f",
                                                  key=f"epr_{txn['id']}")
                    with edit_row[2]:
                        e_gas = st.number_input("手续费", value=txn["gas"],
                                                min_value=0.0, step=1.0, format="%.2f",
                                                key=f"egas_{txn['id']}")
                    with edit_row[3]:
                        try:
                            traded_date = date.fromisoformat(str(txn["traded_at"]))
                        except (ValueError, TypeError):
                            traded_date = date.today()
                        e_traded_at = st.date_input("交易日期", value=traded_date,
                                                    key=f"edate_{txn['id']}")
                    if st.form_submit_button("保存"):
                        e_quantity_val = e_qty if is_buy else -e_qty
                        if _api("PUT", f"/transactions/{txn['id']}", json={
                            "quantity": e_quantity_val,
                            "price": e_price,
                            "gas": e_gas,
                            "traded_at": str(e_traded_at),
                        }):
                            st.success("已更新")
                            st.session_state[f"editing_txn_{txn['id']}"] = False
                            st.rerun()
else:
    st.caption("暂无交易记录")

st.divider()

# ════════════════════════════════════════════
# Block 6: Reports (tabs)
# ════════════════════════════════════════════
st.subheader("📄 分析报告")

reports = _api("GET", f"/stock-analyze/{analyze_id}/reports") or []

if reports:
    tab_titles = [r.get("title", f"报告 {i+1}") for i, r in enumerate(reports)]
    tabs = st.tabs(tab_titles)
    for i, tab in enumerate(tabs):
        with tab:
            r = reports[i]
            st.markdown(f"**{r.get('title', '')}**")
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
