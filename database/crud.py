"""CRUD 数据操作模块。

封装对 Product 和 PriceRecord 表的增删改查操作，
使用 SQLAlchemy 2.0 select 语法。
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from database.models import PriceRecord, Product


# ==================== 商品操作 ====================


def get_or_create_product(
    session: Session,
    title: str,
    url: str,
    sku: Optional[str] = None,
) -> Product:
    """获取或创建商品记录。

    如果 URL 已存在则更新标题和SKU，否则创建新记录。
    使用 flush() 获取 product.id，但不 commit（由调用方控制事务）。

    Args:
        session: 数据库会话
        title: 商品标题
        url: 商品URL
        sku: 商品SKU（可选）

    Returns:
        Product ORM 对象
    """
    stmt = select(Product).where(Product.url == url)
    product = session.execute(stmt).scalar_one_or_none()

    if product is None:
        # 创建新商品
        product = Product(title=title, url=url, sku=sku)
        session.add(product)
        session.flush()  # 刷新以获取自增ID
    else:
        # 更新已有商品信息
        if title and product.title != title:
            product.title = title
        if sku and product.sku != sku:
            product.sku = sku
        product.updated_at = datetime.now()

    return product


def get_all_products(session: Session) -> List[Product]:
    """获取所有商品列表，按更新时间倒序排列。"""
    stmt = select(Product).order_by(desc(Product.updated_at))
    return list(session.execute(stmt).scalars().all())


def get_product_by_id(session: Session, product_id: int) -> Optional[Product]:
    """根据ID获取商品。"""
    return session.get(Product, product_id)


def get_product_by_url(session: Session, url: str) -> Optional[Product]:
    """根据URL获取商品。"""
    stmt = select(Product).where(Product.url == url)
    return session.execute(stmt).scalar_one_or_none()


# ==================== 价格记录操作 ====================


def add_price_record(
    session: Session,
    product_id: int,
    price: float,
    original_price: Optional[float] = None,
    stock: Optional[str] = None,
) -> PriceRecord:
    """添加一条价格记录。

    Args:
        session: 数据库会话
        product_id: 商品ID
        price: 当前价格
        original_price: 原价（可选）
        stock: 库存信息（可选）

    Returns:
        PriceRecord ORM 对象
    """
    record = PriceRecord(
        product_id=product_id,
        price=price,
        original_price=original_price,
        stock=stock,
    )
    session.add(record)
    session.flush()
    return record


def get_latest_price(session: Session, product_id: int) -> Optional[PriceRecord]:
    """获取商品最新一条价格记录。

    Args:
        session: 数据库会话
        product_id: 商品ID

    Returns:
        最新的 PriceRecord，无记录时返回 None
    """
    stmt = (
        select(PriceRecord)
        .where(PriceRecord.product_id == product_id)
        .order_by(desc(PriceRecord.recorded_at))
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def get_price_history(
    session: Session,
    product_id: int,
    limit: int = 50,
) -> List[PriceRecord]:
    """获取商品价格历史记录。

    Args:
        session: 数据库会话
        product_id: 商品ID
        limit: 最多返回条数

    Returns:
        价格记录列表，按时间倒序
    """
    stmt = (
        select(PriceRecord)
        .where(PriceRecord.product_id == product_id)
        .order_by(desc(PriceRecord.recorded_at))
        .limit(limit)
    )
    return list(session.execute(stmt).scalars().all())
