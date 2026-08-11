"""应用配置模块，使用 pydantic-settings 从 .env 文件读取配置。

所有敏感信息（邮箱密码、代理API Key、Cookie等）均从环境变量读取，禁止硬编码。
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局应用配置，字段与 .env 文件中的变量名一一对应（大小写不敏感）。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略 .env 中未定义的变量
    )

    # ==================== 数据库配置 ====================
    #: SQLite 数据库连接字符串
    DATABASE_URL: str = "sqlite:///data/price_monitor.db"

    # ==================== 日志配置 ====================
    #: 日志级别（DEBUG / INFO / WARNING / ERROR）
    LOG_LEVEL: str = "INFO"
    #: 日志输出目录
    LOG_DIR: str = "data/logs"

    # ==================== 爬虫配置 ====================
    #: 最大并发数
    CRAWL_CONCURRENCY: int = 5
    #: 单次请求超时（秒）
    CRAWL_TIMEOUT: int = 30
    #: 失败重试次数
    CRAWL_RETRY: int = 3
    #: 重试间隔基数（秒，每次递增）
    CRAWL_DELAY: float = 1.0

    # ==================== 代理IP配置 ====================
    #: 是否启用代理
    PROXY_ENABLED: bool = False
    #: 代理API地址（从API动态获取代理列表）
    PROXY_API_URL: str = ""
    #: 静态代理列表（逗号分隔，格式：ip:port 或 http://ip:port）
    PROXY_LIST: str = ""

    # ==================== User-Agent 池配置 ====================
    #: 是否启用UA随机轮换
    UA_POOL_ENABLED: bool = True

    # ==================== Cookie 池配置 ====================
    #: 是否启用Cookie池
    COOKIE_POOL_ENABLED: bool = False
    #: Cookie列表（逗号分隔）
    COOKIE_LIST: str = ""

    # ==================== 验证码配置 ====================
    #: 是否启用验证码识别（默认关闭，占位接口）
    CAPTCHA_ENABLED: bool = False
    #: 打码API地址
    CAPTCHA_API_URL: str = ""
    #: 打码API密钥
    CAPTCHA_API_KEY: str = ""

    # ==================== 监控配置 ====================
    #: 定时监控间隔（分钟）
    MONITOR_INTERVAL_MINUTES: int = 30
    #: 价格阈值（大于0时启用，低于此价格触发提醒）
    PRICE_THRESHOLD: float = 0.0

    # ==================== 邮件通知配置 ====================
    #: 是否启用邮件通知
    NOTIFY_ENABLED: bool = False
    #: SMTP 服务器地址
    SMTP_HOST: str = ""
    #: SMTP 端口（465=SSL, 587=TLS）
    SMTP_PORT: int = 465
    #: SMTP 用户名
    SMTP_USER: str = ""
    #: SMTP 密码（从 .env 读取，禁止硬编码）
    SMTP_PASSWORD: str = ""
    #: 发件人地址（为空时使用 SMTP_USER）
    SMTP_FROM: str = ""
    #: 收件人列表（逗号分隔）
    NOTIFY_EMAILS: str = ""

    # ==================== 解析配置（CSS选择器）====================
    #: 商品标题选择器
    SELECTOR_TITLE: str = "h1.product-title"
    #: 当前价格选择器
    SELECTOR_PRICE: str = "span.price"
    #: 原价选择器
    SELECTOR_ORIGINAL_PRICE: str = "span.original-price"
    #: 库存选择器
    SELECTOR_STOCK: str = "span.stock"

    # ==================== 派生属性 ====================

    @property
    def notify_email_list(self) -> List[str]:
        """将逗号分隔的邮箱字符串解析为列表。"""
        if not self.NOTIFY_EMAILS:
            return []
        return [e.strip() for e in self.NOTIFY_EMAILS.split(",") if e.strip()]

    @property
    def proxy_list_parsed(self) -> List[str]:
        """将逗号分隔的代理字符串解析为列表。"""
        if not self.PROXY_LIST:
            return []
        return [p.strip() for p in self.PROXY_LIST.split(",") if p.strip()]

    @property
    def cookie_list_parsed(self) -> List[str]:
        """将逗号分隔的Cookie字符串解析为列表。"""
        if not self.COOKIE_LIST:
            return []
        return [c.strip() for c in self.COOKIE_LIST.split(",") if c.strip()]


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例（使用 lru_cache 缓存，避免重复读取 .env）。"""
    return Settings()
