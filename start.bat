@echo off
chcp 65001 >nul
REM ============================================================
REM 电商商品价格监控爬虫 - 一键启动脚本（Windows）
REM ============================================================
REM 功能：创建虚拟环境 -> 安装依赖 -> 初始化数据库 -> 运行
REM ============================================================

setlocal
cd /d "%~dp0"

echo ========================================
echo   电商商品价格监控爬虫 - 一键启动
echo ========================================

REM 检查 uv 是否安装
where uv >nul 2>nul
if %errorlevel% equ 0 (
    echo [1/4] 使用 uv 创建虚拟环境...
    uv venv .venv
    echo [2/4] 使用 uv 安装依赖...
    uv pip install -r requirements.txt
    call .venv\Scripts\activate.bat
) else (
    echo [提示] 未检测到 uv，使用 pip 替代
    if not exist ".venv" (
        echo [1/4] 创建虚拟环境...
        python -m venv .venv
    ) else (
        echo [1/4] 虚拟环境已存在，跳过创建
    )
    call .venv\Scripts\activate.bat
    echo [2/4] 安装依赖...
    pip install -r requirements.txt
)

REM 创建数据目录
if not exist "data\logs" mkdir data\logs

REM 检查 .env 文件
if not exist ".env" (
    echo [提示] 未找到 .env 文件，从 .env.example 复制...
    copy .env.example .env >nul
    echo [提示] 请根据需要编辑 .env 文件配置邮箱、代理等
)

echo [3/4] 初始化数据库...
python main.py initdb

echo [4/4] 启动程序
echo.
echo 可用命令：
echo   python main.py crawl  ^<URL...^>           # 一次性抓取
echo   python main.py crawl  -f urls.txt          # 从文件读取URL抓取
echo   python main.py monitor -u ^<URL1,URL2^>    # 启动定时监控
echo   python main.py monitor -f urls.txt -i 60   # 每60分钟监控一次
echo   python main.py query                       # 查看所有商品
echo   python main.py query -u ^<URL^>            # 查看指定商品价格历史
echo   python main.py initdb                      # 初始化数据库
echo.
echo 交互式帮助：python main.py --help
echo.

REM 如果有参数，直接执行
if not "%~1"=="" (
    python main.py %*
)

endlocal
