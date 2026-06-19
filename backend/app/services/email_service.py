"""邮件发送服务

封装 SMTP 发送，支持：
- 纯文本邮件
- HTML 邮件（可选）
- 带附件邮件（可选）

配置来源：app.config.settings (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD)

注意：
- 如果 SMTP 未配置，发送操作会记录警告并返回失败，不抛异常
- 默认使用 TLS（端口 587）
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """邮件发送服务"""

    def __init__(self) -> None:
        self._host = settings.smtp_host
        self._port = settings.smtp_port
        self._user = settings.smtp_user
        self._password = settings.smtp_password
        self._enabled = bool(self._host and self._user and self._password)
        if not self._enabled:
            logger.warning("[Email] SMTP 未配置，邮件发送功能已禁用")

    def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        body_html: Optional[str] = None,
        from_name: str = "StockMemos",
    ) -> bool:
        """发送邮件

        Args:
            to: 收件人列表
            subject: 主题
            body: 纯文本正文
            body_html: HTML 正文（可选）
            from_name: 发件人显示名称

        Returns:
            True 如果发送成功，False 如果失败
        """
        if not self._enabled:
            logger.warning("[Email] SMTP 未配置，跳过发送: %s", subject)
            return False

        if not to:
            logger.warning("[Email] 收件人为空，跳过发送")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{self._user}>"
        msg["To"] = ", ".join(to)

        msg.attach(MIMEText(body, "plain", "utf-8"))
        if body_html:
            msg.attach(MIMEText(body_html, "html", "utf-8"))

        try:
            with smtplib.SMTP(self._host, self._port, timeout=30) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.sendmail(self._user, to, msg.as_string())
            logger.info("[Email] 发送成功: %s → %s", subject, to)
            return True
        except Exception as e:
            logger.error("[Email] 发送失败: %s", e)
            return False

    def send_memo_report(
        self,
        to: List[str],
        memos: List[dict],
        watchlist: List[dict],
    ) -> bool:
        """发送备忘录日报邮件"""
        from app.services.report_generator import generate_memo_report

        md_body = generate_memo_report(memos, watchlist, format="markdown")
        subject = f"📊 投研日报 — {len(memos)} 只自选股 ({__import__('datetime').datetime.now().strftime('%Y-%m-%d')})"

        return self.send(
            to=to,
            subject=subject,
            body=md_body,
        )
