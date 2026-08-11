"""Cookie 池模块：从配置加载Cookie列表，支持随机轮换。

用于模拟不同用户会话，降低被反爬系统识别为爬虫的风险。
Cookie 值从 .env 文件读取，禁止硬编码。
"""
from __future__ import annotations

import random
from typing import List, Optional

from loguru import logger

from config.settings import get_settings


class CookiePool:
    """Cookie 池，支持配置化加载与随机轮换。

    当 COOKIE_POOL_ENABLED=True 且配置了 COOKIE_LIST 时启用，
    每次请求随机选择一个Cookie。
    """

    def __init__(self) -> None:
        """初始化Cookie池，从配置加载。"""
        self._cookies: List[str] = []
        self._settings = get_settings()
        self._load_cookies()

    def _load_cookies(self) -> None:
        """从配置加载Cookie列表。"""
        if self._settings.COOKIE_POOL_ENABLED and self._settings.cookie_list_parsed:
            self._cookies = self._settings.cookie_list_parsed.copy()
            logger.info("从配置加载了 {} 个Cookie", len(self._cookies))
        else:
            logger.debug("Cookie池未启用或未配置")

    def get_random(self) -> Optional[str]:
        """随机获取一个Cookie。

        Returns:
            Cookie字符串，无可用Cookie时返回 None
        """
        if not self._cookies:
            return None
        return random.choice(self._cookies)

    def __len__(self) -> int:
        return len(self._cookies)
