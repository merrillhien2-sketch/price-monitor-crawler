"""数据库 CRUD 操作单元测试。

使用 SQLite 内存数据库，测试不依赖外部文件，每次运行都是隔离的。
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.crud import (
    add_price_record,
    get_all_products,
    get_latest_price,
    get_or_create_product,
    get_price_history,
    get_product_by_id,
    get_product_by_url,
)
from database.db import Base


@pytest.fixture
def session():
    """创建内存数据库会话，测试结束后自动销毁。"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    db_session = Session()
    yield db_session
    db_session.close()


class TestProductCRUD:
    """商品表 CRUD 测试。"""

    def test_create_product(self, session) -> None:
        """测试创建新商品。"""
        product = get_or_create_product(
            session, title="测试商品A", url="https://example.com/p/1"
        )
        session.commit()
        assert product.id is not None
        assert product.title == "测试商品A"
        assert product.url == "https://example.com/p/1"

    def test_get_or_create_existing(self, session) -> None:
        """测试获取已存在的商品（不重复创建）。"""
        url = "https://example.com/p/1"
        p1 = get_or_create_product(session, title="商品A", url=url)
        session.commit()
        p2 = get_or_create_product(session, title="商品A-更新标题", url=url)
        session.commit()

        assert p1.id == p2.id
        assert p2.title == "商品A-更新标题"

    def test_get_product_by_id(self, session) -> None:
        """测试按ID查询商品。"""
        product = get_or_create_product(
            session, title="测试商品", url="https://example.com/p/1"
        )
        session.commit()

        found = get_product_by_id(session, product.id)
        assert found is not None
        assert found.title == "测试商品"

    def test_get_product_by_url(self, session) -> None:
        """测试按URL查询商品。"""
        url = "https://example.com/p/999"
        get_or_create_product(session, title="URL测试", url=url)
        session.commit()

        found = get_product_by_url(session, url)
        assert found is not None
        assert found.title == "URL测试"

    def test_get_product_not_found(self, session) -> None:
        """测试查询不存在的商品。"""
        assert get_product_by_id(session, 99999) is None
        assert get_product_by_url(session, "https://example.com/not-exist") is None

    def test_get_all_products(self, session) -> None:
        """测试获取所有商品列表。"""
        get_or_create_product(session, title="商品A", url="https://example.com/p/1")
        get_or_create_product(session, title="商品B", url="https://example.com/p/2")
        session.commit()

        products = get_all_products(session)
        assert len(products) == 2


class TestPriceRecordCRUD:
    """价格记录表 CRUD 测试。"""

    def test_add_price_record(self, session) -> None:
        """测试添加价格记录。"""
        product = get_or_create_product(
            session, title="测试商品", url="https://example.com/p/1"
        )
        session.commit()

        record = add_price_record(
            session, product_id=product.id, price=99.9, original_price=199.9, stock="有货"
        )
        session.commit()

        assert record.id is not None
        assert record.price == 99.9
        assert record.original_price == 199.9
        assert record.stock == "有货"

    def test_get_latest_price(self, session) -> None:
        """测试获取最新价格。"""
        product = get_or_create_product(
            session, title="测试商品", url="https://example.com/p/1"
        )
        session.commit()

        add_price_record(session, product_id=product.id, price=100.0)
        session.commit()
        add_price_record(session, product_id=product.id, price=90.0)
        session.commit()

        latest = get_latest_price(session, product.id)
        assert latest is not None
        assert latest.price == 90.0

    def test_get_latest_price_empty(self, session) -> None:
        """测试无价格记录时获取最新价格。"""
        product = get_or_create_product(
            session, title="测试商品", url="https://example.com/p/1"
        )
        session.commit()

        latest = get_latest_price(session, product.id)
        assert latest is None

    def test_get_price_history(self, session) -> None:
        """测试获取价格历史。"""
        product = get_or_create_product(
            session, title="测试商品", url="https://example.com/p/1"
        )
        session.commit()

        prices = [100.0, 95.0, 90.0]
        for price in prices:
            add_price_record(session, product_id=product.id, price=price)
            session.commit()

        history = get_price_history(session, product.id)
        assert len(history) == 3
        # 倒序排列，最新的在前
        assert history[0].price == 90.0
        assert history[1].price == 95.0
        assert history[2].price == 100.0

    def test_price_history_with_limit(self, session) -> None:
        """测试价格历史条数限制。"""
        product = get_or_create_product(
            session, title="测试商品", url="https://example.com/p/1"
        )
        session.commit()

        for i in range(10):
            add_price_record(session, product_id=product.id, price=float(100 + i))
            session.commit()

        history = get_price_history(session, product.id, limit=5)
        assert len(history) == 5
