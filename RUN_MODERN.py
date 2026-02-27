#!/usr/bin/env python
"""
ARK: Survival Ascended Server Manager - Modern UI Launcher
启动现代化的CustomTkinter版本UI，具有专业的设计和更好的用户体验
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
    
    # 导入并运行modern UI
    from ark_asa_manager.ui.modern_app import launch_modern
    launch_modern()
