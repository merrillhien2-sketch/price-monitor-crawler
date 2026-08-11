"""商品解析器单元测试。

使用本地 mock HTML 文件（tests/sample_product.html）验证解析器的各项功能。
"""
from __future__ import annotations

from pathlib import Path

import pytest

from crawler.parser import ProductParser

# Mock HTML 文件路径
SAMPLE_HTML_PATH = Path(__file__).parent / "sample_product.html"


@pytest.fixture
def sample_html() -> str:
    """加载测试用 HTML 文件。"""
    return SAMPLE_HTML_PATH.read_text(encoding="utf-8")


@pytest.fixture
def parser() -> ProductParser:
    """创建解析器实例。"""
    return ProductParser()


class TestProductParser:
    """ProductParser 解析器测试套件。"""

    def test_parse_title(self, parser: ProductParser, sample_html: str) -> None:
        """测试商品标题解析。"""
        info = parser.parse(sample_html, base_url="https://www.example-shop.com/product/10086")
        assert info is not None
        assert "小米14 Pro" in info.title
        assert "16GB+512GB" in info.title

    def test_parse_price(self, parser: ProductParser, sample_html: str) -> None:
        """测试当前价格解析。"""
        info = parser.parse(sample_html, base_url="https://www.example-shop.com/product/10086")
        assert info is not None
        assert info.price is not None
        assert info.price == 4999.00

    def test_parse_original_price(self, parser: ProductParser, sample_html: str) -> None:
        """测试原价解析。"""
        info = parser.parse(sample_html, base_url="https://www.example-shop.com/product/10086")
        assert info is not None
        assert info.original_price is not None
        assert info.original_price == 5499.00

    def test_parse_stock(self, parser: ProductParser, sample_html: str) -> None:
        """测试库存信息解析。"""
        info = parser.parse(sample_html, base_url="https://www.example-shop.com/product/10086")
        assert info is not None
        assert info.stock == "有货"

    def test_parse_url(self, parser: ProductParser, sample_html: str) -> None:
        """测试URL解析（优先 og:url）。"""
        info = parser.parse(sample_html, base_url="https://www.example-shop.com/product/10086")
        assert info is not None
        assert "10086" in info.url
        assert "example-shop.com" in info.url

    def test_parse_sku(self, parser: ProductParser, sample_html: str) -> None:
        """测试SKU解析（data-sku 属性）。"""
        info = parser.parse(sample_html, base_url="https://www.example-shop.com/product/10086")
        assert info is not None
        assert info.sku == "MI14P-16512-BK"

    def test_parse_empty_html(self, parser: ProductParser) -> None:
        """测试空HTML输入。"""
        info = parser.parse("", base_url="https://example.com")
        assert info is None

    def test_parse_missing_price(self, parser: ProductParser) -> None:
        """测试缺少价格字段的HTML（价格应为None）。"""
        html = '<h1 class="product-title">测试商品</h1>'
        info = parser.parse(html, base_url="https://example.com")
        assert info is not None
        assert info.title == "测试商品"
        assert info.price is None
        assert info.original_price is None

    def test_parse_fallback_title(self, parser: ProductParser) -> None:
        """测试标题备用选择器（无 product-title 类时使用 h1）。"""
        html = '<h1>备用标题测试</h1>'
        info = parser.parse(html, base_url="https://example.com")
        assert info is not None
        assert info.title == "备用标题测试"

    def test_parse_missing_title(self, parser: ProductParser) -> None:
        """测试完全缺少标题的HTML（使用默认值）。"""
        html = '<div>无标题内容</div>'
        info = parser.parse(html, base_url="https://example.com")
        assert info is not None
        assert info.title == "未知商品"

    def test_parse_full_info(self, parser: ProductParser, sample_html: str) -> None:
        """测试完整商品信息解析（综合验证所有字段）。"""
        info = parser.parse(sample_html, base_url="https://www.example-shop.com/product/10086")
        assert info is not None
        assert info.title == "小米14 Pro 16GB+512GB 黑色 5G智能手机"
        assert info.price == 4999.00
        assert info.original_price == 5499.00
        assert info.stock == "有货"
        assert info.sku == "MI14P-16512-BK"
        assert info.url == "https://www.example-shop.com/product/10086"
