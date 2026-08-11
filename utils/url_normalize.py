"""URL 规范化模块：统一URL格式，便于去重和比较。
"""
from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def normalize_url(url: str) -> str:
    """规范化 URL，使其具有唯一表示。

    处理步骤：
    1. 去除首尾空白
    2. scheme 和 host 转小写
    3. 去除 fragment（#后面的部分）
    4. 查询参数排序
    5. 去除路径末尾多余的斜杠

    Args:
        url: 原始 URL 字符串

    Returns:
        规范化后的 URL
    """
    if not url:
        return url

    parsed = urlparse(url.strip())

    # scheme 和 netloc 转小写
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # 去除 fragment
    fragment = ""

    # 查询参数排序
    query_params = sorted(parse_qsl(parsed.query))
    query = urlencode(query_params)

    # 去除路径末尾斜杠（保留根路径 "/"）
    path = parsed.path
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    return urlunparse((scheme, netloc, path, parsed.params, query, fragment))


def is_valid_url(url: str) -> bool:
    """检查 URL 是否有效（包含 scheme 和 netloc）。

    Args:
        url: 待检查的 URL 字符串

    Returns:
        是否为有效 URL
    """
    if not url:
        return False
    try:
        parsed = urlparse(url.strip())
        return bool(parsed.scheme) and bool(parsed.netloc)
    except Exception:
        return False


def extract_domain(url: str) -> str:
    """从 URL 中提取域名（小写）。

    Args:
        url: URL 字符串

    Returns:
        域名字符串，如 "www.example.com"
    """
    parsed = urlparse(url.strip())
    return parsed.netloc.lower()
