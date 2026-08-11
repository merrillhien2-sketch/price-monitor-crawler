"""数据库引擎与会话管理模块。

使用 SQLAlchemy 2.0 风格（DeclarativeBase + typed Mapped），
提供引擎创建、会话上下文管理器和表初始化功能。
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.settings import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明式基类，所有ORM模型继承此类。"""
    pass


# 全局配置实例
_settings = get_settings()

# 创建数据库引擎
# SQLite 需要 check_same_thread=False 以支持多线程/异步场景
_connect_args: dict = {}
if "sqlite" in _settings.DATABASE_URL:
    _connect_args["check_same_thread"] = False

engine = create_engine(
    _settings.DATABASE_URL,
    echo=False,
    connect_args=_connect_args,
)

# 会话工厂
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """创建所有数据库表。

    会自动创建 SQLite 数据库文件所需的目录结构。
    该操作是幂等的：已存在的表不会被重建。
    """
    # 延迟导入模型，确保 ORM 类已注册到 Base.metadata
    from database import models  # noqa: F401

    # 确保 SQLite 数据库文件所在目录存在
    if "sqlite:///" in _settings.DATABASE_URL:
        db_path = _settings.DATABASE_URL.replace("sqlite:///", "")
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """获取数据库会话的上下文管理器。

    使用方式：
        with get_db() as session:
            session.query(...)

    自动处理提交与回滚：
    - 正常退出时自动 commit
    - 发生异常时自动 rollback
    - 无论成功失败都关闭会话
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
