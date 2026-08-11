"""日志配置模块，使用 loguru 实现控制台 + 文件双输出，按天滚动。

日志文件保存在 data/logs/ 目录下，按天滚动，保留30天。
"""
from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from config.settings import get_settings


def setup_logging() -> None:
    """配置 loguru 日志系统。

    - 控制台：彩色格式输出到 stderr
    - 文件：按天滚动，保留30天，UTF-8编码
    """
    settings = get_settings()
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 移除 loguru 默认处理器
    logger.remove()

    # 控制台输出（带颜色）
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    # 文件输出（按天滚动，保留30天）
    logger.add(
        str(log_dir / "price_monitor_{time:YYYY-MM-DD}.log"),
        level=settings.LOG_LEVEL,
        rotation="00:00",          # 每天午夜滚动
        retention="30 days",       # 保留30天
        encoding="utf-8",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        ),
    )

    logger.debug("日志系统初始化完成，输出目录: {}", log_dir)
