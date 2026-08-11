"""商品页面解析模块，使用 BeautifulSoup + lxml 提取商品信息。

解析字段：标题、价格、原价、库存、URL、SKU。
CSS选择器可在 .env 中配置，适配不同电商网站。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from loguru import logger

from config.settings import get_settings
from utils.helpers import parse_price


@dataclass
class ProductInfo:
    """解析得到的商品信息数据结构。"""

    title: str                        #: 商品标题
    price: Optional[float]            #: 当前价格
    original_price: Optional[float]   #: 原价
    stock: Optional[str]              #: 库存信息
    url: str                          #: 商品URL
    sku: Optional[str] = None         #: 商品SKU（可选）


class ProductParser:
    """商品页面解析器，使用可配置的 CSS 选择器提取商品信息。

    选择器通过 .env 配置，默认值适配标准商品页面结构。
    解析失败时会尝试备用选择器，提高兼容性。
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    def parse(self, html: str, base_url: str = "") -> Optional[ProductInfo]:
        """解析商品详情页 HTML，提取商品信息。

        Args:
            html: HTML 字符串
            base_url: 基础URL，用于解析相对链接和作为默认URL

        Returns:
            ProductInfo 对象，HTML为空时返回 None
        """
        if not html:
            logger.warning("HTML内容为空，跳过解析")
            return None

        # 使用 lxml 解析器，不可用时回退到内置解析器
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            logger.debug("lxml 解析器不可用，回退到 html.parser")
            soup = BeautifulSoup(html, "html.parser")

        # ---- 提取标题 ----
        title = self._extract_text(soup, self._settings.SELECTOR_TITLE)
        if not title:
            # 备用选择器：任意 h1 标签
            title = self._extract_text(soup, "h1")
        if not title:
            logger.warning("未能提取商品标题，使用默认值")
            title = "未知商品"

        # ---- 提取当前价格 ----
        price = self._extract_price(soup, self._settings.SELECTOR_PRICE)

        # ---- 提取原价 ----
        original_price = self._extract_price(soup, self._settings.SELECTOR_ORIGINAL_PRICE)

        # ---- 提取库存 ----
        stock = self._extract_text(soup, self._settings.SELECTOR_STOCK)

        # ---- 提取URL ----
        url = self._extract_url(soup, base_url)

        # ---- 提取SKU ----
        sku = self._extract_sku(soup)

        info = ProductInfo(
            title=title.strip(),
            price=price,
            original_price=original_price,
            stock=stock.strip() if stock else None,
            url=url.strip() if url else "",
            sku=sku.strip() if sku else None,
        )

        logger.debug("解析完成: {} - 价格: {}", info.title, info.price)
        return info

    def parse_product_list(self, html: str, base_url: str = "") -> List[str]:
        """从商品列表页 HTML 中解析商品链接。

        支持多种常见的商品链接选择器，提取后进行URL拼接和去重。

        Args:
            html: 列表页 HTML 字符串
            base_url: 基础URL，用于拼接相对链接

        Returns:
            商品URL列表（已去重）
        """
        if not html:
            return []

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            soup = BeautifulSoup(html, "html.parser")

        urls: List[str] = []

        # 常见商品链接选择器（按优先级尝试）
        selectors = [
            "a.product-link",
            "a[class*='product']",
            "a[href*='/product/']",
            "a[href*='/item/']",
            "a[href*='/p/']",
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get("href")
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in urls:
                        urls.append(full_url)
            if urls:
                break

        return urls

    # ==================== 内部方法 ====================

    def _extract_text(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        """使用 CSS 选择器提取元素文本。"""
        if not selector:
            return None
        el = soup.select_one(selector)
        if el:
            return el.get_text(strip=True)
        return None

    def _extract_price(self, soup: BeautifulSoup, selector: str) -> Optional[float]:
        """使用 CSS 选择器提取价格文本并转换为数值。"""
        text = self._extract_text(soup, selector)
        if text:
            return parse_price(text)
        return None

    def _extract_url(self, soup: BeautifulSoup, base_url: str) -> str:
        """提取商品URL（优先 canonical link，其次 og:url）。"""
        # 优先使用 canonical link
        canonical = soup.select_one("link[rel='canonical']")
        if canonical and canonical.get("href"):
            return canonical["href"]

        # 其次使用 Open Graph URL
        og_url = soup.select_one("meta[property='og:url']")
        if og_url and og_url.get("content"):
            return og_url["content"]

        # 回退到 base_url
        return base_url

    def _extract_sku(self, soup: BeautifulSoup) -> Optional[str]:
        """提取商品SKU。"""
        # 尝试 data-sku 属性
        sku_el = soup.select_one("[data-sku]")
        if sku_el:
            sku = sku_el.get("data-sku")
            if sku:
                return sku

        # 尝试 data-product-id 属性
        pid_el = soup.select_one("[data-product-id]")
        if pid_el:
            pid = pid_el.get("data-product-id")
            if pid:
                return pid

        return None
