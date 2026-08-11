"""定时调度模块，使用 APScheduler 实现周期性价格监控。

支持按固定间隔（分钟）触发抓取任务，
配合 AsyncIOScheduler 在 asyncio 事件循环中运行。
"""
from __future__ import annotations

from typing import Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from config.settings import get_settings


class MonitorScheduler:
    """价格监控调度器，管理定时抓取任务。

    使用方式：
        scheduler = MonitorScheduler()
        scheduler.add_crawl_job(my_async_func, interval_minutes=30)
        scheduler.start()
        # ... 运行事件循环 ...
        scheduler.shutdown()
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._scheduler = AsyncIOScheduler()

    def add_crawl_job(
        self,
        func: Callable,
        interval_minutes: Optional[int] = None,
    ) -> None:
        """添加定时抓取任务。

        Args:
            func: 要执行的函数（可以是协程函数）
            interval_minutes: 执行间隔（分钟），为None时使用配置值
        """
        minutes = interval_minutes or self._settings.MONITOR_INTERVAL_MINUTES

        self._scheduler.add_job(
            func,
            trigger=IntervalTrigger(minutes=minutes),
            id="price_monitor",
            replace_existing=True,
            max_instances=1,           # 不允许并发执行同一任务
            coalesce=True,             # 错过多次执行时合并为一次
            misfire_grace_time=60,     # 允许60秒的延迟执行
        )
        logger.info("已添加定时监控任务，间隔 {} 分钟", minutes)

    def start(self) -> None:
        """启动调度器。"""
        self._scheduler.start()
        logger.info("定时监控调度器已启动")

    def shutdown(self) -> None:
        """关闭调度器（不等待正在执行的任务完成）。"""
        self._scheduler.shutdown(wait=False)
        logger.info("定时监控调度器已关闭")

    @property
    def running(self) -> bool:
        """调度器是否正在运行。"""
        return self._scheduler.running
