"""事件时间线页 — 世界热点事件追踪

布局：
    1. 时间线视图：已发生事件 + 待发生事件
    2. 事件卡片：标题、分类、描述、状态
    3. 预测结果：PolyMarket 风格互斥选项
    4. 添加事件表单
"""

import requests
import streamlit as st
from datetime import datetime

API_BASE = "http://backend:8080/api"


def _api(method: str, path: str, **kwargs):
    url = f"{API_BASE}{path}"
    try:
        resp = requests.request(method, url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API 请求失败: {e}")
        return None


st.title("📅 世界热点事件时间线")
st.caption("追踪全球重大事件，维护 PolyMarket 风格预测")

st.markdown("---")

# ── 加载事件列表 ───────────────────────────────
events = _api("GET", "/event-nodes") or []

# ── 添加新事件 ───────────────────────────────
with st.expander("➕ 添加新事件"):
    with st.form("new_event_node"):
        title = st.text_input("事件标题", placeholder="如 美联储2024年12月利率决议")
        category = st.selectbox(
            "分类",
            ["monetary_policy", "geopolitical", "macro_data", "trade_policy", "energy", "tech"],
        )
        occurred_at = st.date_input("已发生日期（如未发生则留空）", value=None)
        description = st.text_area("事件描述")
        source_url = st.text_input("来源链接")
        submitted = st.form_submit_button("保存事件")
        if submitted and title:
            payload = {
                "title": title,
                "category": category,
                "occurred_at": occurred_at.strftime("%Y-%m-%d") if occurred_at else None,
                "description": description or None,
                "source_url": source_url or None,
            }
            result = _api("POST", "/event-nodes", json=payload)
            if result:
                st.success(f"已添加事件: {title}")
                st.rerun()

st.markdown("---")

# ── 事件列表 ───────────────────────────────
if not events:
    st.info("暂无事件，请使用上方表单添加")
else:
    for ev in events:
        status_color = {"pending": "🟡", "occurred": "✅", "materialized": "🔵"}.get(ev.get("status", "pending"), "🟡")
        category_label = ev.get("category", "未分类")
        occurred = f"📅 {ev.get('occurred_at')}" if ev.get("occurred_at") else "⏳ 尚未发生"

        with st.container():
            cols = st.columns([4, 1, 1])
            cols[0].markdown(f"### {status_color} {ev['title']}")
            cols[1].markdown(f"🏷️ {category_label}")
            cols[2].markdown(f"{occurred}")

            if ev.get("description"):
                st.markdown(f"{ev['description']}")

            # 预测结果
            predictions = _api("GET", f"/event-nodes/{ev['id']}/predictions") or []
            if predictions:
                st.markdown("**🔮 预测结果（互斥选项）**")
                for pred in predictions:
                    actual = "✅ 实际结果" if pred.get("is_actual_result") else ""
                    prob = f"({pred.get('probability_estimate', 'N/A') * 100:.0f}%)" if pred.get("probability_estimate") else ""
                    st.markdown(f"- **{pred['outcome_label']}** {prob} {actual}")
                    if pred.get("impact_brief"):
                        st.caption(f"  📌 {pred['impact_brief']}")
            else:
                st.caption("暂无预测结果")

            # 添加预测
            with st.form(f"add_pred_{ev['id']}"):
                c1, c2 = st.columns(2)
                pred_label = c1.text_input("结果标签", placeholder="如 加息25bp", key=f"pl_{ev['id']}")
                pred_prob = c2.number_input("概率估计", min_value=0.0, max_value=1.0, value=0.5, step=0.05, key=f"pp_{ev['id']}")
                pred_desc = st.text_input("结果描述", key=f"pd_{ev['id']}")
                pred_impact = st.text_area("后续影响解析", key=f"pi_{ev['id']}")
                pred_actual = st.checkbox("这是实际结果", key=f"pa_{ev['id']}")
                if st.form_submit_button("添加预测"):
                    if pred_label:
                        payload = {
                            "event_node_id": ev["id"],
                            "outcome_label": pred_label,
                            "outcome_description": pred_desc or None,
                            "probability_estimate": pred_prob,
                            "impact_brief": pred_impact or None,
                            "is_actual_result": pred_actual,
                        }
                        if _api("POST", f"/event-nodes/{ev['id']}/predictions", json=payload):
                            st.success("预测已添加")
                            st.rerun()

            st.markdown("---")
