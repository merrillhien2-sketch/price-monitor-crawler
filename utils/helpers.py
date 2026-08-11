"""工具函数模块：价格解析、格式化、比较、URL去重等辅助功能。
"""
from __future__ import annotations

from typing import List, Optional


def parse_price(price_str: str) -> Optional[float]:
    """从字符串中提取价格数值。

    支持多种格式：
    - "¥4999.00" -> 4999.0
    - "$99.99" -> 99.99
    - "1,299.50" -> 1299.5
    - "￥399" -> 399.0

    Args:
        price_str: 包含价格的字符串

    Returns:
        解析后的浮点价格，解析失败返回 None
    """
    if not price_str:
        return None

    # 去除货币符号、空格、千位分隔符
    cleaned = (
        price_str.strip()
        .replace("¥", "")
        .replace("￥", "")
        .replace("$", "")
        .replace(",", "")
        .replace(" ", "")
        .replace("　", "")  # 全角空格
    )

    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def format_price(price: Optional[float]) -> str:
    """格式化价格用于显示。

    Args:
        price: 价格数值

    Returns:
        格式化后的字符串，如 "¥4999.00"，None 返回 "N/A"
    """
    if price is None:
        return "N/A"
    return f"¥{price:.2f}"


def is_price_drop(
    current: Optional[float],
    previous: Optional[float],
    threshold: float = 0.0,
) -> bool:
    """判断是否触发降价提醒。

    触发条件（满足任一即可）：
    1. 设置了阈值（threshold > 0）且当前价格低于阈值
    2. 有上次价格记录且当前价格低于上次价格

    Args:
        current: 当前价格
        previous: 上次价格（无历史记录时为 None）
        threshold: 价格阈值（0 表示不使用阈值）

    Returns:
        是否应触发降价提醒
    """
    if current is None:
        return False

    # 条件1：低于固定阈值
    if threshold > 0 and current < threshold:
        return True

    # 条件2：低于上次价格
    if previous is not None and current < previous:
        return True

    return False


def price_change_percent(
    current: Optional[float],
    previous: Optional[float],
) -> Optional[float]:
    """计算价格变化百分比。

    Args:
        current: 当前价格
        previous: 上次价格

    Returns:
        变化百分比（正数表示涨价，负数表示降价），无法计算时返回 None
    """
    if current is None or previous is None or previous == 0:
        return None
    return ((current - previous) / previous) * 100


def deduplicate_urls(urls: List[str]) -> List[str]:
    """URL 去重，保持原始顺序。

    Args:
        urls: 可能包含重复的URL列表

    Returns:
        去重后的URL列表
    """
    seen: set = set()
    result: List[str] = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result
