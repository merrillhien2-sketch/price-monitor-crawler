#!/usr/bin/env bash
# ============================================================
# 电商商品价格监控爬虫 - 一键启动脚本（Linux/macOS）
# ============================================================
# 功能：创建虚拟环境 -> 安装依赖 -> 初始化数据库 -> 运行
# 用法：
#   ./start.sh              # 初始化环境并显示帮助
#   ./start.sh initdb       # 初始化数据库
#   ./start.sh crawl <URL>  # 抓取商品
#   ./start.sh monitor -u <URLs>  # 启动定时监控
#   ./start.sh query        # 查询历史
# ============================================================

set -e

# 切换到脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  电商商品价格监控爬虫 - 一键启动"
echo "========================================"

# 检查 uv 是否安装
if command -v uv &> /dev/null; then
    echo "[1/4] 使用 uv 创建虚拟环境..."
    uv venv .venv
    echo "[2/4] 使用 uv 安装依赖..."
    uv pip install -r requirements.txt
    source .venv/bin/activate
else
    echo "[提示] 未检测到 uv，使用 pip 替代"
    # 创建虚拟环境
    if [ ! -d ".venv" ]; then
        echo "[1/4] 创建虚拟环境..."
        python3 -m venv .venv
    else
        echo "[1/4] 虚拟环境已存在，跳过创建"
    fi
    source .venv/bin/activate
    echo "[2/4] 安装依赖..."
    pip install -r requirements.txt
fi

# 创建数据目录
mkdir -p data/logs

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "[提示] 未找到 .env 文件，从 .env.example 复制..."
    cp .env.example .env
    echo "[提示] 请根据需要编辑 .env 文件配置邮箱、代理等"
fi

echo "[3/4] 初始化数据库..."
python main.py initdb

echo "[4/4] 启动程序"
echo ""
echo "可用命令："
echo "  python main.py crawl  <URL...>           # 一次性抓取"
echo "  python main.py crawl  -f urls.txt        # 从文件读取URL抓取"
echo "  python main.py monitor -u <URL1,URL2>    # 启动定时监控"
echo "  python main.py monitor -f urls.txt -i 60 # 每60分钟监控一次"
echo "  python main.py query                      # 查看所有商品"
echo "  python main.py query -u <URL>             # 查看指定商品价格历史"
echo "  python main.py initdb                     # 初始化数据库"
echo ""
echo "交互式帮助：python main.py --help"
echo ""

# 如果有参数，直接执行
if [ $# -gt 0 ]; then
    python main.py "$@"
fi
