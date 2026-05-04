# -*- coding: utf-8 -*-
"""
跨平台路径工具模块。
所有路径操作统一使用 pathlib，避免不同操作系统分隔符差异。
"""

from pathlib import Path


def get_project_root() -> Path:
    """
    通过当前文件位置向上回溯，动态解析项目根目录。

    Returns:
        项目根目录的绝对路径。
    """
    # [Cross-Platform] __file__ 是当前模块路径；
    # resolve() 将其规范化为绝对路径，消除符号链接和相对路径片段
    return Path(__file__).resolve().parent.parent


def get_mock_data_path() -> Path:
    """
    基于项目根目录拼接 mock_data 目录路径。

    Returns:
        mock_data 目录的绝对路径。
    """
    # [Cross-Platform] / 运算符重载用于路径拼接，
    # 运行时根据操作系统自动选择正确的分隔符
    return get_project_root() / "mock_data"
