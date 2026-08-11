"""电商商品价格监控异步爬虫系统 - CLI 入口。

支持四个子命令：
- initdb : 创建数据库表
- crawl  : 一次性抓取商品价格
- monitor: 启动定时价格监控
- query  : 查询价格历史

所有命令均带参数校验与全局异常捕获。
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from config.logging_conf import setup_logging
from config.settings import get_settings
from crawler.downloader import AsyncDownloader
from crawler.parser import ProductParser
from crawler.scheduler import MonitorScheduler
from database.crud import (
    add_price_record,
    get_all_products,
    get_latest_price,
    get_or_create_product,
    get_price_history,
    get_product_by_id,
    get_product_by_url,
)
from database.db import get_db, init_db
from notify.notifier import Notifier
from utils.helpers import format_price, is_price_drop
from utils.url_normalize import is_valid_url, normalize_url

# 初始化日志系统（控制台 + 文件双输出）
setup_logging()

# Rich 控制台输出
console = Console()

# Typer CLI 应用
app = typer.Typer(
    name="price-monitor",
    help="电商商品价格监控异步爬虫系统",
    no_args_is_help=True,
)


def _ensure_db() -> None:
    """确保数据库表已创建（幂等操作）。"""
    try:
        init_db()
    except Exception as e:
        logger.warning("数据库初始化检查失败: {}", e)


def _collect_urls(
    urls: Optional[List[str]],
    file: Optional[str],
) -> List[str]:
    """从命令行参数和文件收集URL列表。

    Args:
        urls: 命令行直接传入的URL列表
        file: 包含URL的文件路径（每行一个URL，#开头为注释）

    Returns:
        有效URL列表
    """
    result: List[str] = []

    # 从命令行参数收集
    if urls:
        for u in urls:
            u = u.strip()
            if is_valid_url(u):
                result.append(u)
            else:
                logger.warning("无效URL，跳过: {}", u)

    # 从文件收集
    if file:
        file_path = Path(file)
        if not file_path.exists():
            console.print(f"[red]文件不存在: {file}[/red]")
            raise typer.Exit(1)
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and is_valid_url(line):
                    result.append(line)

    return result


async def _crawl_and_save(urls: List[str]) -> None:
    """异步抓取商品页面并保存到数据库。

    流程：下载 -> 解析 -> 存库 -> 降价检测 -> 通知

    Args:
        urls: 商品URL列表
    """
    settings = get_settings()
    downloader = AsyncDownloader()
    parser = ProductParser()

    # URL 规范化
    urls = [normalize_url(u) for u in urls]

    console.print(f"[cyan]开始抓取 {len(urls)} 个商品...[/cyan]")

    # 批量异步下载
    results = await downloader.fetch_batch(urls)

    # 解析并保存
    success_count = 0
    for url, html in results.items():
        if html is None:
            logger.warning("下载失败，跳过: {}", url)
            continue

        # 解析商品信息
        info = parser.parse(html, base_url=url)
        if info is None:
            logger.warning("解析失败，跳过: {}", url)
            continue

        # 写入数据库
        with get_db() as session:
            product = get_or_create_product(
                session,
                title=info.title,
                url=info.url,
                sku=info.sku,
            )

            # 获取上次价格（用于降价检测）
            latest = get_latest_price(session, product.id)
            previous_price = latest.price if latest else None

            # 添加新的价格记录
            add_price_record(
                session,
                product_id=product.id,
                price=info.price if info.price is not None else 0.0,
                original_price=info.original_price,
                stock=info.stock,
            )

            # 降价检测与通知
            if is_price_drop(info.price, previous_price, settings.PRICE_THRESHOLD):
                notifier = Notifier()
                notifier.notify_price_drop(
                    product_title=info.title,
                    product_url=info.url,
                    current_price=info.price if info.price is not None else 0.0,
                    previous_price=previous_price,
                    threshold=settings.PRICE_THRESHOLD if settings.PRICE_THRESHOLD > 0 else None,
                )

        success_count += 1
        console.print(
            f"  [green]OK[/green] {info.title} - {format_price(info.price)}"
        )

    console.print(f"\n[green]抓取完成: {success_count}/{len(urls)} 成功[/green]")


# ==================== CLI 命令 ====================


@app.command()
def initdb() -> None:
    """创建数据库表（幂等操作，已存在的表不会重建）。"""
    try:
        init_db()
        console.print("[green]数据库表创建成功[/green]")
        logger.info("数据库表创建成功")
    except Exception as e:
        console.print(f"[red]数据库初始化失败: {e}[/red]")
        logger.error("数据库初始化失败: {}", e)
        raise typer.Exit(1)


@app.command()
def crawl(
    urls: Optional[List[str]] = typer.Argument(
        None, help="商品URL列表（空格分隔多个URL）"
    ),
    file: Optional[str] = typer.Option(
        None, "--file", "-f", help="从文件读取URL（每行一个，#开头为注释）"
    ),
) -> None:
    """一次性抓取商品价格并保存到数据库。"""
    url_list = _collect_urls(urls, file)
    if not url_list:
        console.print("[red]未提供有效的URL，请通过参数或 --file 指定[/red]")
        raise typer.Exit(1)

    _ensure_db()

    try:
        asyncio.run(_crawl_and_save(url_list))
    except KeyboardInterrupt:
        console.print("\n[yellow]用户中断[/yellow]")
    except Exception as e:
        console.print(f"[red]抓取失败: {e}[/red]")
        logger.error("抓取失败: {}", e)
        raise typer.Exit(1)


@app.command()
def monitor(
    urls: Optional[str] = typer.Option(
        None, "--urls", "-u", help="逗号分隔的URL列表"
    ),
    file: Optional[str] = typer.Option(
        None, "--file", "-f", help="从文件读取URL"
    ),
    interval: int = typer.Option(
        0, "--interval", "-i", help="监控间隔（分钟），0=使用配置默认值"
    ),
) -> None:
    """启动定时价格监控（会持续运行，Ctrl+C 停止）。"""
    # 解析URL列表
    url_list_arg = urls.split(",") if urls else None
    url_list = _collect_urls(url_list_arg, file)
    if not url_list:
        console.print("[red]未提供有效的URL，请通过 --urls 或 --file 指定[/red]")
        raise typer.Exit(1)

    # 校验间隔参数
    if interval < 0:
        console.print("[red]间隔分钟数不能为负数[/red]")
        raise typer.Exit(1)

    settings = get_settings()
    interval_minutes = interval if interval > 0 else settings.MONITOR_INTERVAL_MINUTES

    _ensure_db()

    console.print(
        f"[cyan]启动定时监控：间隔 {interval_minutes} 分钟，"
        f"共 {len(url_list)} 个商品[/cyan]"
    )

    async def run_monitor() -> None:
        """监控主循环。"""
        scheduler = MonitorScheduler()

        async def crawl_job() -> None:
            """定时触发的抓取任务。"""
            logger.info("=== 定时任务触发：开始抓取 ===")
            try:
                await _crawl_and_save(url_list)
            except Exception as e:
                logger.error("定时抓取异常: {}", e)

        # 添加定时任务
        scheduler.add_crawl_job(crawl_job, interval_minutes)
        scheduler.start()

        # 首次立即执行一次
        await crawl_job()

        # 保持事件循环运行
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            scheduler.shutdown()

    try:
        asyncio.run(run_monitor())
    except KeyboardInterrupt:
        console.print("\n[yellow]监控已停止[/yellow]")


@app.command()
def query(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="按URL查询"),
    product_id: Optional[int] = typer.Option(None, "--id", help="按商品ID查询"),
    limit: int = typer.Option(20, "--limit", "-n", help="显示条数"),
) -> None:
    """查询价格历史记录。"""
    # 参数校验
    if limit < 1:
        console.print("[red]显示条数必须大于0[/red]")
        raise typer.Exit(1)

    _ensure_db()

    with get_db() as session:
        # 按URL或ID查询特定商品
        if url:
            product = get_product_by_url(session, normalize_url(url))
        elif product_id:
            product = get_product_by_id(session, product_id)
        else:
            # 无参数时列出所有商品
            products = get_all_products(session)
            if not products:
                console.print("[yellow]暂无商品记录[/yellow]")
                return

            table = Table(title="商品列表")
            table.add_column("ID", style="cyan", justify="right")
            table.add_column("标题", style="white")
            table.add_column("URL", style="blue")
            table.add_column("最新价格", style="green", justify="right")

            for p in products:
                latest = get_latest_price(session, p.id)
                price_str = format_price(latest.price) if latest else "N/A"
                # URL 截断显示
                display_url = p.url if len(p.url) <= 60 else p.url[:57] + "..."
                table.add_row(str(p.id), p.title, display_url, price_str)

            console.print(table)
            console.print(
                "\n[dim]提示：使用 --url 或 --id 查看特定商品的价格历史[/dim]"
            )
            return

        if not product:
            console.print("[red]未找到商品[/red]")
            raise typer.Exit(1)

        # 查询价格历史
        history = get_price_history(session, product.id, limit=limit)

        console.print(f"\n[bold]商品: {product.title}[/bold]")
        console.print(f"URL: {product.url}")
        console.print(f"SKU: {product.sku or 'N/A'}")

        if not history:
            console.print("[yellow]暂无价格记录[/yellow]")
            return

        table = Table(title=f"价格历史（最近 {len(history)} 条）")
        table.add_column("时间", style="cyan")
        table.add_column("价格", style="green", justify="right")
        table.add_column("原价", style="yellow", justify="right")
        table.add_column("库存", style="white")

        for record in history:
            table.add_row(
                record.recorded_at.strftime("%Y-%m-%d %H:%M:%S"),
                format_price(record.price),
                format_price(record.original_price),
                record.stock or "N/A",
            )

        console.print(table)


def main() -> None:
    """主入口函数，带全局异常捕获。"""
    try:
        app()
    except Exception as e:
        logger.error("程序异常退出: {}", e, exc_info=True)
        console.print(f"[red]程序异常: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
