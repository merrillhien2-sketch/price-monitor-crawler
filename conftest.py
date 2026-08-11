"""Pytest 全局配置，确保项目根目录在 Python 路径中。"""
from __future__ import annotations

import sys
from pathlib import Path

# 将项目根目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent))
