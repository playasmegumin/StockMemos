"""自选股与投资备忘录页 — 核心页面

布局：
    1. 左侧：自选股列表（可添加/删除）
    2. 右侧：选中股票的备忘录编辑器
        - 估值区域（目标股价、估值方法）
        - 重要事件列表（添加/编辑/删除）
        - 业务分析（文本编辑）
        - 趋势预测（短线/中线/长期 + 核心逻辑）
        - 用户备注
        - Agent 触发按钮（基本面/消息/技术）
"""

import requests
import streamlit as st
from datetime import datetime

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


def _safe_index(options, value, fallback=0):
    """安全获取 value 在 options 中的索引，永不崩溃。"""
    if not options:
        return fallback
    if value is None:
        return fallback
    try:
        return options.index(value)
    except (ValueError, TypeError):
        return fallback


# ── 页面标题 ───────────────────────────────
st.title("🔖 自选股与投资备忘录")
st.caption("维护关注列表，为每只股票建立投研备忘录")

# ── 布局：左侧列表 + 右侧编辑器 ─────────────
left, right = st.columns([1, 2])

# ════════════════════════════════════════════
# 左侧：自选股列表
# ════════════════════════════════════════════
with left:
    st.subheader("📋 自选股")
    
    # 添加自选股表单
    with st.expander("➕ 添加"):
        with st.form("add_watchlist"):
            code = st.text_input("股票代码", placeholder="如 000001.SZ")
            name = st.text_input("股票名称", placeholder="如 平安银行")
            sector = st.text_input("板块", placeholder="如 银行")
            submitted = st.form_submit_button("添加")
        
        if submitted and code:
            result = _api("POST", "/watchlist", json={
                "stock_code": code,
                "stock_name": name or None,
                "sector": sector or None,
            })
            if result:
                st.success(f"已添加 {code}")
                st.rerun()
    
    # 加载列表
    watchlist = _api("GET", "/watchlist") or []
    
    if not watchlist:
        st.info("暂无自选股，请使用上方表单添加")
        selected_code = None
    else:
        # 用 session_state 记住选中项
        if "selected_stock" not in st.session_state:
            st.session_state.selected_stock = watchlist[0]["stock_code"]
        
        for item in watchlist:
            cols = st.columns([4, 1])
            label = f"{item['stock_code']}"
            if item.get("stock_name"):
                label += f" · {item['stock_name']}"
            if item.get("sector"):
                label += f" ({item['sector']})"
            
            if cols[0].button(label, key=f"select_{item['id']}", use_container_width=True):
                st.session_state.selected_stock = item["stock_code"]
                st.rerun()
            
            if cols[1].button("🗑️", key=f"del_wl_{item['id']}"):
                if _api("DELETE", f"/watchlist/{item['id']}"):
                    st.success(f"已移除 {item['stock_code']}")
                    if st.session_state.selected_stock == item["stock_code"]:
                        st.session_state.selected_stock = None
                    st.rerun()
        
        selected_code = st.session_state.get("selected_stock")

# ════════════════════════════════════════════
# 右侧：备忘录编辑器
# ════════════════════════════════════════════
with right:
    if not selected_code:
        st.info("👈 请在左侧选择一只自选股")
    else:
        # 加载备忘录
        memo = _api("GET", f"/watchlist/{selected_code}/memo") or {}
        events = _api("GET", f"/watchlist/{selected_code}/memo/events") or []
        
        st.markdown(f"### 📝 {selected_code} 投资备忘录")
        st.markdown("---")
        
        # ── 1. 估值区域 ─────────────────────
        with st.expander("💰 估值", expanded=True):
            with st.form(f"memo_valuation_{selected_code}"):
                c1, c2 = st.columns(2)
                target_price = c1.number_input(
                    "目标股价",
                    value=memo.get("target_price", 0.0) or 0.0,
                    step=0.01,
                    format="%.2f",
                )
                _VALUATION_OPTIONS = ["PE", "DCF", "可比公司", "PB", "PS", "其他"]
                _current_val = memo.get("valuation_method")
                _val_idx = _safe_index(_VALUATION_OPTIONS, _current_val, 0)
                valuation_method = c2.selectbox(
                    "估值方法",
                    _VALUATION_OPTIONS,
                    index=_val_idx,
                )
                submitted = st.form_submit_button("💾 保存估值")
            
            if submitted:
                payload = {
                    "stock_code": selected_code,
                    "target_price": target_price if target_price > 0 else None,
                    "valuation_method": valuation_method,
                    "business_scope": memo.get("business_scope"),
                    "short_trend": memo.get("short_trend"),
                    "mid_trend": memo.get("mid_trend"),
                    "long_trend": memo.get("long_trend"),
                    "trend_logic": memo.get("trend_logic"),
                    "notes": memo.get("notes"),
                }
                result = _api("PUT", f"/watchlist/{selected_code}/memo", json=payload)
                if result:
                    st.success("估值已保存")
                    st.rerun()
        
        # ── 2. 重要事件 ─────────────────────
        with st.expander("📅 重要事件", expanded=True):
            if events:
                for ev in events:
                    cols = st.columns([3, 1, 1, 1])
                    cols[0].markdown(f"**{ev['event_name']}**")
                    tag = ev.get("impact_tag", "")
                    tag_color = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(tag, "⚪")
                    cols[1].markdown(f"{tag_color} {tag}")
                    cols[2].markdown(f"📅 {ev.get('expected_date', '待定')}")
                    status = ev.get("result_status", "pending")
                    status_label = {"pending": "⏳", "occurred": "✅", "expired": "❌", "cancelled": "🚫"}.get(status, "⏳")
                    cols[3].markdown(f"{status_label} {status}")
                    
                    with st.popover(f"编辑 {ev['event_name']}"):
                        with st.form(f"edit_event_{ev['id']}"):
                            ev_name = st.text_input("事件名称", value=ev["event_name"])
                            _EV_TYPES = ["earnings", "order", "geopolitical", "policy", "other"]
                            _ev_type = ev.get("event_type", "other")
                            ev_type = st.selectbox("类型", _EV_TYPES, index=_safe_index(_EV_TYPES, _ev_type, 4))
                            _IMPACTS = ["bullish", "bearish", "neutral"]
                            _ev_impact = ev.get("impact_tag", "neutral")
                            ev_impact = st.selectbox("影响", _IMPACTS, index=_safe_index(_IMPACTS, _ev_impact, 2))
                            ev_date = st.date_input("预期日期", value=datetime.strptime(ev["expected_date"], "%Y-%m-%d").date() if ev.get("expected_date") else datetime.today())
                            _STATUSES = ["pending", "occurred", "expired", "cancelled"]
                            _ev_status = ev.get("result_status", "pending")
                            ev_status = st.selectbox("状态", _STATUSES, index=_safe_index(_STATUSES, _ev_status, 0))
                            ev_summary = st.text_area("结果摘要", value=ev.get("result_summary", ""))
                            ev_source = st.text_input("来源", value=ev.get("source_url", ""))
                            save_ev = st.form_submit_button("保存")
                        
                        if save_ev:
                            payload = {
                                "memo_id": ev["memo_id"],
                                "event_name": ev_name,
                                "event_type": ev_type,
                                "impact_tag": ev_impact,
                                "expected_date": ev_date.strftime("%Y-%m-%d"),
                                "result_status": ev_status,
                                "result_summary": ev_summary or None,
                                "source_url": ev_source or None,
                            }
                            if _api("PUT", f"/watchlist/{selected_code}/memo/events/{ev['id']}", json=payload):
                                st.success("事件已更新")
                                st.rerun()
                        
                        if st.button("删除事件", key=f"del_ev_{ev['id']}"):
                            if _api("DELETE", f"/watchlist/{selected_code}/memo/events/{ev['id']}"):
                                st.success("已删除")
                                st.rerun()
            
            # 添加新事件
            with st.form(f"add_event_{selected_code}"):
                st.markdown("**➕ 添加新事件**")
                c1, c2 = st.columns(2)
                new_name = c1.text_input("事件名称", placeholder="如 Q3 财报发布")
                new_type = c2.selectbox("类型", ["earnings", "order", "geopolitical", "policy", "other"])
                c3, c4 = st.columns(2)
                new_impact = c3.selectbox("影响", ["bullish", "bearish", "neutral"])
                new_date = c4.date_input("预期日期", value=datetime.today())
                new_source = st.text_input("来源链接")
                add_submitted = st.form_submit_button("添加事件")
            
            if add_submitted and new_name:
                payload = {
                    "memo_id": memo.get("id", ""),
                    "event_name": new_name,
                    "event_type": new_type,
                    "impact_tag": new_impact,
                    "expected_date": new_date.strftime("%Y-%m-%d"),
                    "source_url": new_source or None,
                }
                if _api("POST", f"/watchlist/{selected_code}/memo/events", json=payload):
                    st.success(f"已添加事件: {new_name}")
                    st.rerun()
        
        # ── 3. 业务分析 ─────────────────────
        with st.expander("🏭 业务分析"):
            business_scope = st.text_area(
                "业务范围 / 供需关系 / 产业链生态位",
                value=memo.get("business_scope", ""),
                height=150,
                key=f"biz_{selected_code}",
            )
            if st.button("💾 保存业务分析", key=f"save_biz_{selected_code}"):
                payload = {
                    "stock_code": selected_code,
                    "target_price": memo.get("target_price"),
                    "valuation_method": memo.get("valuation_method"),
                    "business_scope": business_scope or None,
                    "short_trend": memo.get("short_trend"),
                    "mid_trend": memo.get("mid_trend"),
                    "long_trend": memo.get("long_trend"),
                    "trend_logic": memo.get("trend_logic"),
                    "notes": memo.get("notes"),
                }
                if _api("PUT", f"/watchlist/{selected_code}/memo", json=payload):
                    st.success("业务分析已保存")
                    st.rerun()
        
        # ── 4. 趋势预测 ─────────────────────
        with st.expander("📈 趋势预测"):
            c1, c2, c3 = st.columns(3)
            _TREND_OPTIONS = ["up", "down", "sideways"]
            short_trend = c1.selectbox("短线", _TREND_OPTIONS, index=_safe_index(_TREND_OPTIONS, memo.get("short_trend"), 2))
            mid_trend = c2.selectbox("中线", _TREND_OPTIONS, index=_safe_index(_TREND_OPTIONS, memo.get("mid_trend"), 2))
            long_trend = c3.selectbox("长期", _TREND_OPTIONS, index=_safe_index(_TREND_OPTIONS, memo.get("long_trend"), 2))
            trend_logic = st.text_area("核心逻辑", value=memo.get("trend_logic", ""), height=120)
            if st.button("💾 保存趋势预测", key=f"save_trend_{selected_code}"):
                payload = {
                    "stock_code": selected_code,
                    "target_price": memo.get("target_price"),
                    "valuation_method": memo.get("valuation_method"),
                    "business_scope": memo.get("business_scope"),
                    "short_trend": short_trend,
                    "mid_trend": mid_trend,
                    "long_trend": long_trend,
                    "trend_logic": trend_logic or None,
                    "notes": memo.get("notes"),
                }
                if _api("PUT", f"/watchlist/{selected_code}/memo", json=payload):
                    st.success("趋势预测已保存")
                    st.rerun()
        
        # ── 5. 用户备注 ─────────────────────
        with st.expander("📝 备注"):
            notes = st.text_area("自定义备注", value=memo.get("notes", ""), height=100)
            if st.button("💾 保存备注", key=f"save_notes_{selected_code}"):
                payload = {
                    "stock_code": selected_code,
                    "target_price": memo.get("target_price"),
                    "valuation_method": memo.get("valuation_method"),
                    "business_scope": memo.get("business_scope"),
                    "short_trend": memo.get("short_trend"),
                    "mid_trend": memo.get("mid_trend"),
                    "long_trend": memo.get("long_trend"),
                    "trend_logic": memo.get("trend_logic"),
                    "notes": notes or None,
                }
                if _api("PUT", f"/watchlist/{selected_code}/memo", json=payload):
                    st.success("备注已保存")
                    st.rerun()
        
        st.markdown("---")
        
        # ── 6. Agent 触发按钮 ─────────────────
        st.subheader("🤖 Agent 智能分析")
        st.caption("点击按钮触发 Agent 分析，自动更新备忘录对应字段")
        
        ac1, ac2, ac3 = st.columns(3)
        
        # FundamentalAgent
        if ac1.button("🔍 基本面分析", use_container_width=True, type="primary", key=f"agent_fund_{selected_code}"):
            with st.spinner("FundamentalAgent 分析中..."):
                result = _api("POST", f"/analyze/{selected_code}/fundamental")
            if result:
                if result.get("status") == "success":
                    st.success("✅ 基本面分析完成，备忘录已更新")
                    with st.expander("📋 查看分析详情"):
                        r = result.get("result", {})
                        st.markdown(f"**估值方法**: {r.get('valuation_method', 'N/A')}")
                        st.markdown(f"**目标价**: {r.get('target_price', 'N/A')}")
                        st.markdown(f"**置信度**: {r.get('confidence', 'N/A')}")
                        st.markdown("**业务分析**:")
                        st.markdown(r.get("business_scope", "") or "无")
                        st.markdown("**分析逻辑**:")
                        st.markdown(r.get("reasoning", "") or "无")
                    st.rerun()
                else:
                    st.error(f"分析失败: {result.get('result', {}).get('error', '未知错误')}")
        
        # NewsAgent
        if ac2.button("📰 消息分析", use_container_width=True, type="primary", key=f"agent_news_{selected_code}"):
            with st.spinner("NewsAgent 分析中（含多空辩论）..."):
                result = _api("POST", f"/analyze/{selected_code}/news")
            if result:
                if result.get("status") == "success":
                    st.success("✅ 消息分析完成，备忘录已更新")
                    with st.expander("📋 查看分析详情"):
                        r = result.get("result", {})
                        st.markdown(f"**综合判断**: {r.get('consensus', 'N/A')}")
                        st.markdown(f"**推荐**: {r.get('recommendation', 'N/A')}")
                        st.markdown("**看多理由**:")
                        bull = r.get("bull_case", {})
                        for arg in bull.get("arguments", []):
                            st.markdown(f"- {arg}")
                        st.markdown("**看空理由**:")
                        bear = r.get("bear_case", {})
                        for arg in bear.get("arguments", []):
                            st.markdown(f"- {arg}")
                        st.markdown("**事件列表**:")
                        for ev in r.get("events", []):
                            tag_color = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(ev.get("impact_tag"), "⚪")
                            st.markdown(f"- {tag_color} **{ev.get('name')}** ({ev.get('expected_date', '待定')})")
                        st.markdown("**分析逻辑**:")
                        st.markdown(r.get("reasoning", "") or "无")
                    st.rerun()
                else:
                    st.error(f"分析失败: {result.get('result', {}).get('error', '未知错误')}")
        
        # TechnicalAgent
        if ac3.button("📈 技术分析", use_container_width=True, type="primary", key=f"agent_tech_{selected_code}"):
            with st.spinner("TechnicalAgent 分析中..."):
                result = _api("POST", f"/analyze/{selected_code}/technical")
            if result:
                if result.get("status") == "success":
                    st.success("✅ 技术分析完成，备忘录已更新")
                    with st.expander("📋 查看分析详情"):
                        r = result.get("result", {})
                        st.markdown(f"**短线**: {r.get('short_trend', 'N/A')}")
                        st.markdown(f"**中线**: {r.get('mid_trend', 'N/A')}")
                        st.markdown(f"**长期**: {r.get('long_trend', 'N/A')}")
                        st.markdown(f"**置信度**: {r.get('confidence', 'N/A')}")
                        kl = r.get("key_levels", {})
                        st.markdown(f"**支撑位**: {kl.get('support', 'N/A')}")
                        st.markdown(f"**阻力位**: {kl.get('resistance', 'N/A')}")
                        st.markdown("**趋势逻辑**:")
                        st.markdown(r.get("trend_logic", "") or "无")
                        st.markdown("**分析逻辑**:")
                        st.markdown(r.get("reasoning", "") or "无")
                    st.rerun()
                else:
                    st.error(f"分析失败: {result.get('result', {}).get('error', '未知错误')}")
