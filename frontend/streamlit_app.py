"""StockMemos 首页 — 持仓概览与股票列表"""

import sys
sys.path.append("/app")

import requests
import streamlit as st
from datetime import date, datetime, timezone, timedelta
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
# 持仓概览
# ════════════════════════════════════════════
st.title("📈 持仓概览")

with st.spinner("正在加载数据..."):
    stocks_data = _api("GET", "/stocks")

if stocks_data is None:
    stocks_data = []

# 首次加载检测（仅在新浏览器 session 时触发）
_data_init = st.session_state.get("data_initialized")
if stocks_data and not _data_init:
    first_sid = stocks_data[0]["id"]
    kline = _api("GET", f"/stocks/{first_sid}/kline?end={date.today().isoformat()}", silent=True)
    if isinstance(kline, list) and len(kline) == 0:
        with st.spinner("首次加载，正在初始化行情数据..."):
            _api("POST", "/market/refresh", silent=True)
    st.session_state["data_initialized"] = True

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
# 股票列表
# ════════════════════════════════════════════
st.subheader("📋 股票列表")

refresh_col, _ = st.columns([1, 5])
with refresh_col:
    if st.button("🔄 刷新基本面", key="refresh_fundamentals"):
        with st.spinner("正在刷新基本面数据..."):
            result = _api("POST", "/market/refresh-fundamentals")
            if result:
                st.success("基本面刷新完成")
                st.rerun()
            else:
                st.error("基本面刷新失败")

if not stocks_data:
    st.info("暂无股票数据。")
else:
    # 获取标签摘要
    tag_map = {}
    for s in stocks_data:
        analyze = _api("GET", f"/stock-analyze/stock/{s['id']}")
        if analyze and analyze.get("id"):
            tags = _api("GET", f"/stock-analyze/{analyze['id']}/stock-tags")
            if tags:
                tag_map[s["id"]] = [t["tag"] for t in tags]

    # 获取实时价格（仅 session 首次触发，之后缓存到 session_state）
    price_map = st.session_state.get("price_data_cache", {})
    if not price_map and stocks_data:
        for s in stocks_data:
            pd = _api("GET", f"/stocks/{s['id']}/price", silent=True)
            if pd:
                price_map[s["id"]] = pd
        if price_map:
            st.session_state["price_data_cache"] = price_map

    for s in stocks_data:
        sid = s["id"]
        pos = float(s.get("position", 0))
        pnl = float(s.get("historical_pnl", 0))
        code_str = f"{s['symbol']}.{s['exchange']}"
        tags_html = " ".join(f'<span class="tag-pill">{t}</span>'
                            for t in tag_map.get(sid, []))
        pd = price_map.get(sid)

        # 浮动盈亏 = 最新价 × 持仓 + 历史盈亏
        price_val = float(pd["price"]) if pd else None
        floating_pnl = price_val * pos + pnl if (price_val and pos) else pnl

        with st.container(border=True):
            cols = st.columns([2, 2, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
            with cols[0]:
                st.markdown(f"**{s['name']}**  \n<small>{code_str}</small>",
                           unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"货币: {s['currency']}")
            with cols[2]:
                if pd:
                    ts = _fmt_time(pd.get("price_time"))
                    st.markdown(
                        f"**最新价**  \n{price_val:.2f}"
                        + (f" <small style='color:#888'>{ts}</small>" if ts else ""),
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown("**最新价**  \n<small>当前不可用</small>", unsafe_allow_html=True)
            with cols[3]:
                st.markdown(f"**持仓**  \n{pos:,.0f}")
            with cols[4]:
                pnl_style = "positive" if floating_pnl >= 0 else "negative"
                st.markdown(
                    f"**浮动盈亏**  \n<span style='color:{'#e74c3c' if floating_pnl >= 0 else '#27ae60'}'>{'%+.2f' % floating_pnl}</span>",
                    unsafe_allow_html=True,
                )
            with cols[5]:
                if tags_html:
                    st.markdown(f"<small>{tags_html}</small>", unsafe_allow_html=True)
                else:
                    st.markdown("<small>—</small>", unsafe_allow_html=True)
            with cols[6]:
                if st.button("🔍 详情", key=f"detail_{sid}"):
                    st.session_state["current_stock_id"] = sid
                    st.switch_page("pages/stock_detail.py")
            with cols[7]:
                if st.button("🗑️ 删除", key=f"del_{sid}"):
                    if _api("DELETE", f"/stocks/{sid}"):
                        st.rerun()

st.divider()

# ════════════════════════════════════════════
# 添加股票（内联行，置于列表底部）
# ════════════════════════════════════════════
st.subheader("➕ 添加股票")

EXCHANGE_OPTIONS = ["CN - CNY", "SH - CNY", "SZ - CNY", "HK - HKD", "US - USD"]

add_row = st.columns([2, 2, 2, 0.8])
with add_row[0]:
    code = st.text_input("股票代码", placeholder="600519 / 00700 / AAPL",
                         key="add_code")
with add_row[1]:
    selected_exchange = st.selectbox("交易所代号", options=EXCHANGE_OPTIONS,
                                     key="add_exchange")
    exchange = selected_exchange.split(" - ")[0]
    currency = selected_exchange.split(" - ")[1]

# 自动查询：代码+交易所组合变化时自动获取名称+货币
lookup_key = f"{exchange}:{code.strip()}"
prev_lookup = st.session_state.get("last_lookup")
if code.strip() and lookup_key != prev_lookup:
    st.session_state["last_lookup"] = lookup_key
    result = _api("GET", f"/stocks/lookup?symbol={code.strip()}&exchange={exchange}", silent=True)
    if result and result.get("name"):
        st.session_state["add_name"] = result["name"]
        # 自动设置货币（如 HK→HKD）
        target_opt = next((o for o in EXCHANGE_OPTIONS if o.endswith(result["currency"])), None)
        if target_opt:
            st.session_state["add_exchange"] = target_opt
        st.rerun()

with add_row[2]:
    name = st.text_input("股票名称", placeholder="贵州茅台",
                         key="add_name")

with add_row[3]:
    if st.button("＋ 添加", key="add_stock_btn", use_container_width=True):
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
                st.rerun()
