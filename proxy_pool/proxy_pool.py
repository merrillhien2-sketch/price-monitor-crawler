"""代理IP池模块：从配置加载代理列表，提供随机获取与健康检查功能。

支持两种代理来源：
1. 静态列表（PROXY_LIST 配置项，逗号分隔）
2. 代理API（PROXY_API_URL 配置项，需自行实现具体API调用）

简易健康检查：通过请求 httpbin.org/ip 测试代理可用性，
失败代理会被标记并剔除。
"""
from __future__ import annotations

import asyncio
import random
from typing import List, Optional, Set

import aiohttp
from loguru import logger

from config.settings import get_settings


class ProxyPool:
    """代理IP池，支持健康检查与失败剔除。"""

    def __init__(self) -> None:
        """初始化代理池，从配置加载代理列表。"""
        self._proxies: List[str] = []
        self._bad_proxies: Set[str] = set()
        self._settings = get_settings()
        self._load_proxies()

    def _load_proxies(self) -> None:
        """从配置加载代理列表。"""
        # 从静态列表加载
        static_list = self._settings.proxy_list_parsed
        if static_list:
            self._proxies = static_list.copy()
            logger.info("从配置加载了 {} 个代理IP", len(self._proxies))

        # 从代理API加载（占位：需根据实际API文档实现）
        if self._settings.PROXY_API_URL:
            logger.info("代理API URL已配置: {}，需实现具体API调用逻辑",
                        self._settings.PROXY_API_URL)
            # TODO: 实现从代理API获取代理列表
            # proxies = self._fetch_from_api(self._settings.PROXY_API_URL)
            # self._proxies.extend(proxies)

    def get_proxy(self) -> Optional[str]:
        """随机获取一个可用代理。

        Returns:
            代理地址（如 "http://1.2.3.4:8080"），无可用代理时返回 None
        """
        available = [p for p in self._proxies if p not in self._bad_proxies]
        if not available:
            return None
        return random.choice(available)

    def mark_bad(self, proxy: str) -> None:
        """标记代理为不可用（下载失败时调用）。"""
        self._bad_proxies.add(proxy)
        logger.warning("代理 {} 已标记为不可用", proxy)

    def mark_good(self, proxy: str) -> None:
        """标记代理为可用（下载成功时调用，恢复之前被标记的代理）。"""
        self._bad_proxies.discard(proxy)

    async def health_check(self) -> None:
        """简易健康检查：并发测试所有代理是否可用。

        通过请求 httpbin.org/ip 测试代理连通性，
        超时或返回非200的代理会被标记为不可用。
        """
        if not self._proxies:
            return

        test_url = "https://httpbin.org/ip"
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._check_one(session, proxy, test_url)
                for proxy in self._proxies
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

        available = [p for p in self._proxies if p not in self._bad_proxies]
        logger.info("代理健康检查完成：{}/{} 可用", len(available), len(self._proxies))

    async def _check_one(
        self,
        session: aiohttp.ClientSession,
        proxy: str,
        test_url: str,
    ) -> None:
        """检查单个代理的可用性。"""
        try:
            proxy_url = proxy if proxy.startswith("http") else f"http://{proxy}"
            timeout = aiohttp.ClientTimeout(total=10)
            async with session.get(test_url, proxy=proxy_url, timeout=timeout) as resp:
                if resp.status == 200:
                    self.mark_good(proxy)
                else:
                    self.mark_bad(proxy)
        except Exception:
            self.mark_bad(proxy)

    @property
    def is_empty(self) -> bool:
        """是否有可用代理。"""
        return len(self) == 0

    def __len__(self) -> int:
        """可用代理数量。"""
        return len([p for p in self._proxies if p not in self._bad_proxies])
