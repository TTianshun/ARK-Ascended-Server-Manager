#!/usr/bin/env python3
"""
快速 EXE 构建脚本 - 一键打包
只需运行这个脚本，自动完成所有步骤
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    project_root = Path(__file__).parent
    
    print("\n" + "="*60)
    print("ARK Ascended Server Manager - 一键打包")
    print("="*60 + "\n")
    
    # Step 1: 检查依赖
    print("[1/3] 检查并安装依赖...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements.txt",
            "-q"  # 静默输出
        ], cwd=project_root, check=True)
        print("  ✓ 应用依赖已安装")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ 失败: {e}")
        return False
    
    # Step 2: 安装打包工具
    print("[2/3] 安装打包工具...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "pyinstaller>=6.0.0",
            "-q"
        ], cwd=project_root, check=True)
        print("  ✓ PyInstaller 已安装")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ 失败: {e}")
        return False
    
    # Step 3: 构建 EXE
    print("[3/3] 构建 EXE 文件...")
    try:
        result = subprocess.run([
            sys.executable,
            "build_exe.py",
            "--onefile",
            "--clean"
        ], cwd=project_root)
        
        if result.returncode == 0:
            exe_path = project_root / "dist" / "ARK-Ascended-Server-Manager.exe"
            print("\n" + "="*60)
            print("✓ 打包完成！")
            print("="*60)
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"\n文件位置: {exe_path}")
                print(f"文件大小: {size_mb:.2f} MB")
                print("\n你现在可以运行生成的 EXE 文件了!")
            return True
        else:
            print("\n✗ 构建失败")
            return False
            
    except Exception as e:
        print(f"  ✗ 失败: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
