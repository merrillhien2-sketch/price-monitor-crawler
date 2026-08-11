"""ORM 数据模型定义模块。

使用 SQLAlchemy 2.0 typed style（Mapped / mapped_column）定义：
- Product：商品表，记录商品基本信息
- PriceRecord：价格记录表，记录每次抓取的价格快照
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base


class Product(Base):
    """商品表：存储商品的基本信息。

    每个商品通过 URL 唯一标识，同一URL多次抓取只创建一条记录。
    """

    __tablename__ = "products"

    #: 主键ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    #: 商品标题
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="商品标题")
    #: 商品URL（唯一索引，用于去重）
    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True, comment="商品URL")
    #: 商品SKU（可选）
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="商品SKU")
    #: 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, comment="创建时间"
    )
    #: 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    #: 关联的价格记录列表（一对多，级联删除）
    price_records: Mapped[List["PriceRecord"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, title={self.title!r})>"


class PriceRecord(Base):
    """价格记录表：每次抓取保存一条价格快照。

    通过 product_id 外键关联到 Product 表，
    支持查询商品的历史价格走势。
    """

    __tablename__ = "price_records"

    #: 主键ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    #: 关联商品ID（外键，级联删除）
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        comment="商品ID",
    )
    #: 当前价格
    price: Mapped[float] = mapped_column(Float, nullable=False, comment="当前价格")
    #: 原价（可选，用于显示折扣信息）
    original_price: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="原价"
    )
    #: 库存信息（字符串，如"有货"/"仅剩3件"）
    stock: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="库存信息"
    )
    #: 记录时间
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, comment="记录时间"
    )

    #: 关联的商品对象（多对一）
    product: Mapped["Product"] = relationship(back_populates="price_records")

    def __repr__(self) -> str:
        return f"<PriceRecord(id={self.id}, product_id={self.product_id}, price={self.price})>"
