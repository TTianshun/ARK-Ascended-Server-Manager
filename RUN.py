#!/usr/bin/env python
"""
ARK: Survival Ascended Server Manager 快速启动脚本
直接运行: python RUN.py 或双击此文件
"""
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    # 添加项目src目录到路径
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    sys.path.insert(0, str(src_dir))
    
    # 改变工作目录
    os.chdir(project_root)
    
    # 导入并运行
    from ark_asa_manager.__main__ import launch
    launch()
