"""异步下载器模块，基于 aiohttp 实现高性能并发下载。

特性：
- asyncio.Semaphore 控制最大并发数
- 自动重试（可配置次数，指数退避间隔）
- 请求超时控制
- 代理IP池集成（失败自动剔除）
- User-Agent 随机轮换
- Cookie 池支持
- 全局异常捕获与日志记录
"""
from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

import aiohttp
from loguru import logger

from anti_detect.cookie_pool import CookiePool
from config.settings import get_settings
from proxy_pool.proxy_pool import ProxyPool
from proxy_pool.ua_pool import UAPool


class AsyncDownloader:
    """异步下载器，支持重试、超时、并发控制、代理与UA轮换。

    使用方式：
        downloader = AsyncDownloader()
        html = await downloader.fetch("https://example.com/product/123")
        # 批量下载
        results = await downloader.fetch_batch(["url1", "url2", "url3"])
    """

    def __init__(self) -> None:
        """初始化下载器，读取配置并创建辅助组件。"""
        self._settings = get_settings()
        self._semaphore = asyncio.Semaphore(self._settings.CRAWL_CONCURRENCY)
        self._ua_pool = UAPool()
        self._proxy_pool = ProxyPool() if self._settings.PROXY_ENABLED else None
        self._cookie_pool = CookiePool()
        self._timeout = aiohttp.ClientTimeout(total=self._settings.CRAWL_TIMEOUT)

    async def fetch(self, url: str) -> Optional[str]:
        """异步下载单个URL内容，带并发控制与重试机制。

        Args:
            url: 目标URL

        Returns:
            HTML内容字符串，所有重试均失败时返回 None
        """
        async with self._semaphore:
            return await self._fetch_with_retry(url)

    async def _fetch_with_retry(self, url: str) -> Optional[str]:
        """带重试的下载逻辑。

        重试次数由 CRAWL_RETRY 配置控制，
        每次重试间隔递增（CRAWL_DELAY * 尝试次数）。
        """
        max_retries = self._settings.CRAWL_RETRY
        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                result = await self._do_fetch(url)
                if result is not None:
                    return result
                # 返回None但未抛异常（如HTTP 403），也视为失败重试
                logger.warning("下载返回空结果 (尝试 {}/{}): {}", attempt, max_retries, url)
            except asyncio.CancelledError:
                # 取消异常不重试，直接传播
                raise
            except Exception as e:
                last_error = e
                logger.warning(
                    "下载异常 (尝试 {}/{}): {} - {}",
                    attempt, max_retries, url, e,
                )

            # 未达到最大重试次数时等待
            if attempt < max_retries:
                wait_time = self._settings.CRAWL_DELAY * attempt
                logger.debug("等待 {:.1f}s 后重试...", wait_time)
                await asyncio.sleep(wait_time)

        logger.error("下载最终失败: {} - 最后错误: {}", url, last_error)
        return None

    async def _do_fetch(self, url: str) -> Optional[str]:
        """执行单次HTTP GET请求。

        集成UA轮换、代理、Cookie等反爬策略。
        代理失败时自动标记为不可用。
        """
        headers = self._build_headers()
        proxy = self._get_proxy()

        try:
            async with aiohttp.ClientSession(timeout=self._timeout) as session:
                async with session.get(
                    url,
                    headers=headers,
                    proxy=proxy,
                    allow_redirects=True,
                ) as response:
                    if response.status != 200:
                        logger.warning("HTTP {}: {}", response.status, url)
                        if response.status == 403:
                            logger.warning("可能被反爬拦截（403）: {}", url)
                        return None

                    # 下载成功，标记代理为可用
                    if proxy and self._proxy_pool:
                        self._proxy_pool.mark_good(proxy)

                    html = await response.text()
                    logger.debug("下载成功: {} ({} bytes)", url, len(html))
                    return html

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            # 网络错误，标记代理为不可用
            if proxy and self._proxy_pool:
                self._proxy_pool.mark_bad(proxy)
            raise

    async def fetch_batch(self, urls: List[str]) -> Dict[str, Optional[str]]:
        """批量异步下载多个URL。

        并发数由 CRAWL_CONCURRENCY 控制（通过信号量），
        所有URL并发提交，失败不影响其他URL。

        Args:
            urls: URL列表

        Returns:
            字典：{url: html_content or None}
        """
        if not urls:
            return {}

        logger.info("开始批量下载 {} 个URL", len(urls))
        tasks = [self.fetch(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output: Dict[str, Optional[str]] = {}
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error("批量下载异常: {} - {}", url, result)
                output[url] = None
            else:
                output[url] = result

        success = sum(1 for v in output.values() if v is not None)
        logger.info("批量下载完成: {}/{} 成功", success, len(urls))
        return output

    # ==================== 内部方法 ====================

    def _build_headers(self) -> Dict[str, str]:
        """构建HTTP请求头，集成UA轮换与Cookie。"""
        headers: Dict[str, str] = {
            "User-Agent": self._ua_pool.get_random(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        cookie = self._cookie_pool.get_random()
        if cookie:
            headers["Cookie"] = cookie
        return headers

    def _get_proxy(self) -> Optional[str]:
        """获取代理URL。

        从代理池随机选取，无可用代理时返回None（直连）。
        """
        if self._proxy_pool and not self._proxy_pool.is_empty:
            proxy = self._proxy_pool.get_proxy()
            if proxy:
                # 确保代理URL有协议前缀
                return proxy if proxy.startswith("http") else f"http://{proxy}"
        return None
