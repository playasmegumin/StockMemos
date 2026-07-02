"""StockMemos 首页 — 持仓概览与股票列表"""

import sys
sys.path.append("/app")

import requests
import streamlit as st
from app.components.sidebar import render_sidebar

st.set_page_config(
    page_title="持仓概览",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ─────────────────────────────
st.markdown("""
    <style>
    .stApp .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    .card { background: #fff; border-radius: 10px; padding: 1.2rem 1.5rem;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08); text-align: center; }
    .card-label { font-size: 0.85rem; color: #888; margin-bottom: 0.3rem; }
    .card-value { font-size: 1.5rem; font-weight: 700; color: #1a1a2e; }
    .card-value.positive { color: #e74c3c; }
    .card-value.negative { color: #27ae60; }
    .tag-pill { display: inline-block; background: #eef2ff; color: #4f46e5;
                border-radius: 12px; padding: 2px 10px; font-size: 0.8rem;
                margin: 1px 2px; }
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
# 持仓概览
# ════════════════════════════════════════════
st.title("📈 持仓概览")

with st.spinner("正在加载数据..."):
    stocks_data = _api("GET", "/stocks")

if stocks_data is None:
    stocks_data = []

# ── 汇总卡片 ──
total_position = sum(float(s.get("position", 0)) for s in stocks_data)
total_pnl = sum(float(s.get("historical_pnl", 0)) for s in stocks_data)
stock_count = len(stocks_data)

cols = st.columns(4)
pnl_style = "positive" if total_pnl >= 0 else "negative"

with cols[0]:
    st.markdown(f"""<div class='card'>
        <div class='card-label'>股票数量</div>
        <div class='card-value'>{stock_count}</div>
    </div>""", unsafe_allow_html=True)
with cols[1]:
    st.markdown(f"""<div class='card'>
        <div class='card-label'>总持仓量</div>
        <div class='card-value'>{total_position:,.0f}</div>
    </div>""", unsafe_allow_html=True)
with cols[2]:
    st.markdown(f"""<div class='card'>
        <div class='card-label'>历史盈亏</div>
        <div class='card-value {pnl_style}'>{'%+.2f' % total_pnl}</div>
    </div>""", unsafe_allow_html=True)
with cols[3]:
    st.markdown(f"""<div class='card'>
        <div class='card-label'>持仓股票</div>
        <div class='card-value'>{sum(1 for s in stocks_data if float(s.get("position", 0)) != 0)}</div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ════════════════════════════════════════════
# 添加股票
# ════════════════════════════════════════════
st.subheader("➕ 添加股票")

exchange_currency_map = {
    "CN": "CNY", "SH": "CNY", "SZ": "CNY",
    "HK": "HKD", "US": "USD",
}

with st.form("add_stock_form"):
    row = st.columns([3, 2, 3, 1])
    with row[0]:
        code = st.text_input("股票代码", placeholder="600519 / 00700 / AAPL")
    with row[1]:
        exchange = st.selectbox("交易所", options=list(exchange_currency_map.keys()))
    with row[2]:
        name = st.text_input("股票名称", placeholder="贵州茅台")
    with row[3]:
        currency = exchange_currency_map[exchange]
        st.text_input("货币", value=currency, disabled=True)

    submitted = st.form_submit_button("添加", use_container_width=True)
    if submitted:
        if not code.strip() or not name.strip():
            st.error("股票代码和名称不能为空")
        else:
            result = _api("POST", "/stocks", json={
                "exchange": exchange,
                "symbol": code.strip(),
                "name": name.strip(),
                "currency": currency,
            })
            if result:
                st.success(f"已添加: {name.strip()}")
                st.rerun()

# ════════════════════════════════════════════
# 股票列表
# ════════════════════════════════════════════
st.subheader("📋 股票列表")

if not stocks_data:
    st.info("暂无股票数据，请在上方添加第一支股票。")
else:
    # 获取标签摘要
    tag_map = {}
    for s in stocks_data:
        analyze = _api("GET", f"/stock-analyze/stock/{s['id']}")
        if analyze and analyze.get("id"):
            tags = _api("GET", f"/stock-analyze/{analyze['id']}/stock-tags")
            if tags:
                tag_map[s["id"]] = [t["tag"] for t in tags]

    for s in stocks_data:
        sid = s["id"]
        pos = float(s.get("position", 0))
        pnl = float(s.get("historical_pnl", 0))
        code_str = f"{s['exchange']}.{s['symbol']}"
        tags_html = " ".join(f'<span class="tag-pill">{t}</span>'
                            for t in tag_map.get(sid, []))

        with st.container(border=True):
            cols = st.columns([2, 2, 1.5, 1.5, 1.5, 1.5, 2])
            with cols[0]:
                st.markdown(f"**{s['name']}**  \n<small>{code_str}</small>",
                           unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"货币: {s['currency']}")
            with cols[2]:
                st.markdown(f"**持仓**  \n{pos:,.0f}")
            with cols[3]:
                st.markdown(f"**盈亏**  \n{'%+.2f' % pnl}")
            with cols[4]:
                if tags_html:
                    st.markdown(f"<small>{tags_html}</small>", unsafe_allow_html=True)
                else:
                    st.markdown("<small>—</small>", unsafe_allow_html=True)
            with cols[5]:
                if st.button("🔍 详情", key=f"detail_{sid}"):
                    st.session_state["current_stock_id"] = sid
                    st.switch_page("pages/stock_detail.py")
            with cols[6]:
                if st.button("🗑️ 删除", key=f"del_{sid}"):
                    if _api("DELETE", f"/stocks/{sid}"):
                        st.rerun()
