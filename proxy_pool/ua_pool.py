"""User-Agent 池模块：管理UA列表，支持随机轮换以模拟不同浏览器。

默认内置6种主流浏览器UA，可通过配置启用/禁用随机轮换。
"""
from __future__ import annotations

import random
from typing import List, Optional

from config.settings import get_settings

# 内置常用 User-Agent 列表（覆盖主流浏览器和操作系统）
DEFAULT_UA_LIST: List[str] = [
    # Chrome - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",
    # Chrome - macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Safari - macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Chrome - Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Edge - Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
]


class UAPool:
    """User-Agent 池，支持随机轮换。

    当 UA_POOL_ENABLED=True 时，每次请求随机选择一个UA；
    否则固定使用第一个UA。
    """

    def __init__(self, ua_list: Optional[List[str]] = None) -> None:
        """初始化UA池。

        Args:
            ua_list: 自定义UA列表，为None时使用默认列表
        """
        settings = get_settings()

        if ua_list:
            # 使用自定义列表
            self._ua_list = ua_list
        elif settings.UA_POOL_ENABLED:
            # 启用随机轮换，使用完整默认列表
            self._ua_list = DEFAULT_UA_LIST.copy()
        else:
            # 禁用轮换，仅使用第一个UA
            self._ua_list = [DEFAULT_UA_LIST[0]]

    def get_random(self) -> str:
        """随机获取一个 User-Agent。"""
        return random.choice(self._ua_list)

    def get_first(self) -> str:
        """获取第一个 User-Agent（不随机）。"""
        return self._ua_list[0]

    def __len__(self) -> int:
        return len(self._ua_list)
