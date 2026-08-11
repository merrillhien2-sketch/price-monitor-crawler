"""降价通知模块：当检测到价格下降时，通过邮件和日志发送提醒。

邮件发送使用 smtplib，支持 SSL（端口465）和 TLS（端口587）。
SMTP密码从 .env 文件读取，禁止硬编码。
通知开关由 NOTIFY_ENABLED 控制。
"""
from __future__ import annotations

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from loguru import logger

from config.settings import get_settings


class Notifier:
    """降价通知器，支持邮件通知和日志记录。

    触发条件（在 main.py 中判断）：
    1. 当前价格低于配置的阈值 PRICE_THRESHOLD
    2. 当前价格低于上次记录的价格

    通知方式：
    - 日志：始终记录（不受 NOTIFY_ENABLED 控制）
    - 邮件：仅在 NOTIFY_ENABLED=True 且 SMTP 配置完整时发送
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    def notify_price_drop(
        self,
        product_title: str,
        product_url: str,
        current_price: float,
        previous_price: Optional[float],
        threshold: Optional[float] = None,
    ) -> None:
        """发送降价提醒通知。

        Args:
            product_title: 商品标题
            product_url: 商品URL
            current_price: 当前价格
            previous_price: 上次价格（首次记录时为 None）
            threshold: 阈值价格（未设置阈值时为 None）
        """
        # 构建通知内容
        subject = f"[降价提醒] {product_title}"
        lines = [
            f"商品名称: {product_title}",
            f"商品链接: {product_url}",
            f"当前价格: \u00a5{current_price:.2f}",
        ]

        if previous_price is not None:
            drop_amount = previous_price - current_price
            drop_percent = (drop_amount / previous_price) * 100 if previous_price > 0 else 0.0
            lines.append(f"上次价格: \u00a5{previous_price:.2f}")
            lines.append(f"降价金额: \u00a5{drop_amount:.2f}")
            lines.append(f"降价幅度: {drop_percent:.1f}%")

        if threshold is not None:
            lines.append(f"提醒阈值: \u00a5{threshold:.2f}")

        lines.append(f"提醒时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        body = "\n".join(lines)

        # 始终记录日志
        logger.info("检测到降价！通知内容:\n{}", body)

        # 发送邮件（受开关控制）
        if self._settings.NOTIFY_ENABLED and self._settings.notify_email_list:
            self._send_email(subject, body)
        else:
            logger.debug("邮件通知未启用或未配置收件人，仅记录日志")

    def _send_email(self, subject: str, body: str) -> None:
        """发送邮件通知。

        根据 SMTP_PORT 自动选择 SSL（465）或 STARTTLS（其他端口）。
        SMTP密码从配置读取，不在代码中硬编码。
        """
        settings = self._settings

        # 检查SMTP配置是否完整
        if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
            logger.warning("SMTP配置不完整（HOST/USER/PASSWORD），跳过邮件发送")
            return

        try:
            # 构建邮件
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
            msg["To"] = ", ".join(settings.notify_email_list)
            msg.attach(MIMEText(body, "plain", "utf-8"))

            # 根据端口选择加密方式
            if settings.SMTP_PORT == 465:
                # SSL 直连
                with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(
                        settings.SMTP_USER,
                        settings.notify_email_list,
                        msg.as_string(),
                    )
            else:
                # STARTTLS
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(
                        settings.SMTP_USER,
                        settings.notify_email_list,
                        msg.as_string(),
                    )

            logger.info("降价邮件已发送至: {}", ", ".join(settings.notify_email_list))

        except smtplib.SMTPAuthenticationError as e:
            logger.error("SMTP认证失败，请检查用户名和密码: {}", e)
        except smtplib.SMTPException as e:
            logger.error("SMTP发送异常: {}", e)
        except Exception as e:
            logger.error("邮件发送失败（未知异常）: {}", e)
