# 电商商品价格监控异步爬虫系统

基于 **aiohttp + asyncio + SQLAlchemy 2.0 + APScheduler** 构建的高性能异步爬虫系统，支持商品价格定时监控与降价邮件提醒。

## 项目简介

本项目是一个电商商品价格监控系统，采用异步并发架构，能够高效抓取商品页面、解析价格信息、存储到数据库，并在价格下降时通过邮件和日志发送提醒。系统内置代理IP池、User-Agent池、Cookie池等反爬策略，适用于中长期价格监控场景。

## 核心功能

1. **异步并发抓取**：基于 aiohttp + asyncio，信号量控制并发数，自动重试（3次）与超时处理
2. **商品信息解析**：使用 BeautifulSoup + lxml 提取标题、价格、原价、库存、URL、SKU
3. **ORM 存储**：SQLAlchemy 2.0 typed style，SQLite 存储，支持商品去重与价格历史查询
4. **定时监控**：APScheduler 定时抓取，价格低于阈值或较上次下降时触发降价提醒
5. **邮件通知**：smtplib 发送降价邮件，支持 SSL/TLS，全部配置化
6. **反爬策略**：代理IP池（健康检查+失败剔除）、UA随机轮换、Cookie池、验证码占位接口
7. **CLI 命令行**：typer 构建，支持 `crawl` / `monitor` / `query` / `initdb` 四个子命令
8. **日志系统**：loguru 控制台 + 文件双输出，按天滚动，保留30天

## 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 异步HTTP | aiohttp >= 3.9 | 高性能异步下载 |
| 异步框架 | asyncio | 事件循环 |
| HTML解析 | BeautifulSoup4 + lxml | CSS选择器提取 |
| ORM | SQLAlchemy 2.0 | typed Mapped 风格 |
| 数据库 | SQLite | 轻量级文件数据库 |
| 定时任务 | APScheduler | IntervalTrigger 定时调度 |
| 配置管理 | pydantic-settings | 从 .env 读取配置 |
| 日志 | loguru | 结构化日志，按天滚动 |
| 邮件 | smtplib | 降价提醒邮件 |
| CLI | typer + rich | 命令行界面与美化输出 |
| 测试 | pytest | 单元测试 |

## 系统架构

```
                    +------------------+
                    |     main.py      |  CLI 入口（typer）
                    |  crawl/monitor/  |
                    |  query/initdb    |
                    +--------+---------+
                             |
          +------------------+------------------+
          |                  |                  |
+---------v--------+ +------v-------+ +--------v--------+
| crawler/         | | database/    | | notify/         |
| downloader.py    | | db.py        | | notifier.py     |
| parser.py        | | models.py    | | (邮件+日志)      |
| scheduler.py     | | crud.py      | +-----------------+
+---------+--------+ +------+-------+
          |                 |
+---------v--------+        |
| proxy_pool/      |        |
| ua_pool.py       |        |
| proxy_pool.py    |        |
+------------------+        |
|                  |
+---------v--------+        |
| anti_detect/     |        |
| cookie_pool.py   |        |
| captcha.py       |        |
+------------------+--------+
                             |
                    +--------v---------+
                    |   config/        |
                    | settings.py      |  pydantic-settings
                    | logging_conf.py  |  loguru 日志配置
                    +------------------+
```

## 环境要求

- Python 3.10+（兼容 3.10.12，目标 3.11+）
- pip 或 uv（推荐 uv 加速安装）

## 快速开始

### 一键启动（推荐）

```bash
# Linux/macOS
chmod +x start.sh
./start.sh

# Windows
start.bat
```

脚本会自动完成：创建虚拟环境 -> 安装依赖 -> 复制配置 -> 初始化数据库 -> 显示帮助。

### 手动安装

```bash
# 1. 创建虚拟环境
uv venv .venv          # 或 python3 -m venv .venv

# 2. 激活虚拟环境
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows

# 3. 安装依赖
uv pip install -r requirements.txt    # 或 pip install -r requirements.txt

# 4. 复制配置文件
cp .env.example .env

# 5. 初始化数据库
python main.py initdb
```

## 使用方法

### 1. 一次性抓取（crawl）

```bash
# 直接传入URL
python main.py crawl https://example.com/product/1 https://example.com/product/2

# 从文件读取URL（每行一个，#开头为注释）
python main.py crawl -f urls.txt
```

### 2. 启动定时监控（monitor）

```bash
# 使用配置默认间隔（30分钟）
python main.py monitor -u https://example.com/product/1,https://example.com/product/2

# 自定义间隔（60分钟）
python main.py monitor -u https://example.com/product/1 -i 60

# 从文件读取URL
python main.py monitor -f urls.txt -i 15
```

### 3. 查询价格历史（query）

```bash
# 列出所有商品
python main.py query

# 按URL查询价格历史
python main.py query -u https://example.com/product/1

# 按商品ID查询，显示最近50条
python main.py query --id 1 -n 50
```

### 4. 初始化数据库（initdb）

```bash
python main.py initdb
```

## 配置说明

所有配置通过 `.env` 文件管理（从 `.env.example` 复制）。关键配置项：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| DATABASE_URL | sqlite:///data/price_monitor.db | 数据库连接 |
| CRAWL_CONCURRENCY | 5 | 最大并发数 |
| CRAWL_TIMEOUT | 30 | 请求超时（秒） |
| CRAWL_RETRY | 3 | 失败重试次数 |
| MONITOR_INTERVAL_MINUTES | 30 | 监控间隔（分钟） |
| PRICE_THRESHOLD | 0 | 价格阈值（>0时启用） |
| PROXY_ENABLED | false | 是否启用代理 |
| NOTIFY_ENABLED | false | 是否启用邮件通知 |
| SMTP_HOST | (空) | SMTP服务器地址 |
| SMTP_PASSWORD | (空) | SMTP密码（从.env读取） |
| SELECTOR_TITLE | h1.product-title | 标题CSS选择器 |
| SELECTOR_PRICE | span.price | 价格CSS选择器 |

## 目录结构

```
price-monitor-crawler/
├── config/                  # 配置层
│   ├── __init__.py
│   ├── settings.py          # pydantic-settings 配置读取
│   └── logging_conf.py      # loguru 日志配置
├── database/                # 数据库层
│   ├── __init__.py
│   ├── db.py                # 引擎/会话/初始化
│   ├── models.py            # Product/PriceRecord ORM
│   └── crud.py              # 增删改查封装
├── crawler/                 # 爬虫核心
│   ├── __init__.py
│   ├── downloader.py        # aiohttp 异步下载（重试/超时/并发）
│   ├── parser.py            # BeautifulSoup 解析商品页
│   └── scheduler.py         # APScheduler 定时调度
├── proxy_pool/              # 反爬：代理与UA
│   ├── __init__.py
│   ├── proxy_pool.py        # 代理IP池（健康检查）
│   └── ua_pool.py           # User-Agent 池
├── anti_detect/             # 反爬：Cookie与验证码
│   ├── __init__.py
│   ├── cookie_pool.py       # Cookie 池
│   └── captcha.py           # 验证码占位（带开关）
├── notify/                  # 通知层
│   ├── __init__.py
│   └── notifier.py          # 降价提醒（邮件+日志）
├── utils/                   # 工具层
│   ├── __init__.py
│   ├── helpers.py           # 价格解析/比较/格式化
│   └── url_normalize.py     # URL规范化
├── tests/                   # 测试
│   ├── __init__.py
│   ├── test_parser.py       # 解析器测试
│   ├── test_crud.py         # CRUD测试
│   └── sample_product.html  # 测试用Mock HTML
├── data/                    # 运行时数据（.gitignore）
│   └── .gitkeep
├── conftest.py              # pytest配置
├── main.py                  # CLI入口
├── requirements.txt         # 依赖列表
├── .gitignore
├── .env.example             # 配置模板
├── start.sh                 # 一键启动（Linux/macOS）
├── start.bat                # 一键启动（Windows）
├── README.md                # 项目说明（本文件）
└── 使用文档.md               # 详细使用文档
```

## 自检说明

项目支持以下自检方式：

```bash
# 1. 语法检查（编译所有Python文件）
python -m compileall .

# 2. 初始化数据库
python main.py initdb

# 3. 运行测试
python -m pytest tests/ -v

# 4. 查看CLI帮助
python main.py --help
```

## 安全说明

- 所有密码、密钥、Token 均通过 `.env` 文件读取，**禁止硬编码到代码中**
- `.env` 文件已在 `.gitignore` 中排除，不会提交到版本控制
- `.env.example` 仅包含占位符（如 `your_smtp_password`），无真实密钥
- 验证码模块默认关闭，API密钥从配置读取

## 许可证

本项目仅供学习和个人使用。
