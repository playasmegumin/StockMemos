"""设置与投递页

功能：
    1. RSS 订阅链接展示（备忘录、策略信号）
    2. 邮件配置状态检查
    3. 测试邮件发送
    4. 导出报告（Markdown/JSON）
"""

import requests
import streamlit as st

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
    url = f"{API_BASE}{path}"
    try:
        resp = requests.request(method, url, timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API 请求失败: {e}")
        return None


# ── 页面标题 ───────────────────────────────
st.title("⚙️ 设置与投递")
st.caption("RSS 订阅、邮件推送、报告导出")

# ── RSS 订阅 ──────────────────────────────
st.subheader("📡 RSS 订阅")
st.markdown("使用 RSS 阅读器订阅以下链接，自动接收投研更新：")

base_url = "http://localhost:8080"

r1, r2 = st.columns(2)
with r1:
    st.markdown("**📊 自选股备忘录**")
    st.code(f"{base_url}/api/output/memos?format=rss", language="html")
    st.markdown(f"[查看 Markdown 格式]({base_url}/api/output/memos?format=markdown)")

with r2:
    st.markdown("**🎯 策略信号**")
    st.code(f"{base_url}/api/output/strategy-signals?format=rss", language="html")
    st.markdown(f"[查看 Markdown 格式]({base_url}/api/output/strategy-signals?format=markdown)")

st.markdown("---")

# ── 邮件推送 ──────────────────────────────
st.subheader("📧 邮件推送")

with st.form("email_test"):
    email_to = st.text_input("收件人邮箱", placeholder="your@email.com")
    send_btn = st.form_submit_button("📤 发送备忘录日报")

if send_btn and email_to:
    with st.spinner("发送中..."):
        result = _api("POST", "/output/email/memos", json={"to": [email_to]})
    if result:
        if result.get("status") == "sent":
            st.success(f"✅ 邮件已发送至 {email_to}")
        else:
            st.warning(f"⚠️ 发送失败（SMTP 可能未配置）\n\n后端返回: {result}")

st.markdown("---")

# ── 报告导出 ──────────────────────────────
st.subheader("📥 报告导出")

c1, c2 = st.columns(2)
with c1:
    st.markdown("**投资备忘录报告**")
    st.markdown(f"[Markdown]({base_url}/api/output/memos?format=markdown)")
    st.markdown(f"[JSON]({base_url}/api/output/memos?format=json)")
    st.markdown(f"[RSS XML]({base_url}/api/output/memos?format=rss)")

with c2:
    st.markdown("**策略信号报告**")
    st.markdown(f"[Markdown]({base_url}/api/output/strategy-signals?format=markdown)")
    st.markdown(f"[JSON]({base_url}/api/output/strategy-signals?format=json)")
    st.markdown(f"[RSS XML]({base_url}/api/output/strategy-signals?format=rss)")
