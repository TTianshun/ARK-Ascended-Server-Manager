#!/usr/bin/env python3
"""
ARK: Survival Ascended Server Manager - EXE 打包脚本
使用 PyInstaller 将应用打包成单个 EXE 文件

使用方法:
    python build_exe.py [选项]

选项:
    --onefile      生成单文件 exe (默认)
    --onedir       生成文件夹格式 (更快的启动速度)
    --windowed     隐藏控制台窗口 (默认)
    --console      显示控制台窗口
    --clean        清理之前的构建文件
    --no-upx       不使用 UPX 压缩
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()
SRC_DIR = PROJECT_ROOT / "src"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
SPEC_FILE = PROJECT_ROOT / "ark_asa_manager.spec"

# 应用信息
APP_NAME = "ARK-Ascended-Server-Manager"
MAIN_MODULE = "ark_asa_manager"
ENTRY_POINT = SRC_DIR / MAIN_MODULE / "__main__.py"


def clean_build_files():
    """清理之前的构建文件"""
    print("清理之前的构建文件...")
    for directory in [BUILD_DIR, DIST_DIR, SPEC_FILE]:
        if isinstance(directory, Path) and directory.exists():
            if directory.is_file():
                directory.unlink()
                print(f"  删除: {directory}")
            else:
                shutil.rmtree(directory)
                print(f"  删除: {directory}")


def install_pyinstaller():
    """安装 PyInstaller"""
    try:
        import PyInstaller
        print("PyInstaller 已安装")
    except ImportError:
        print("安装 PyInstaller...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "pyinstaller>=5.0.0", "--upgrade"
        ])


def build_exe(onefile=True, windowed=True, clean=False, upx=True):
    """
    构建 EXE 文件
    
    Args:
        onefile: 是否生成单文件 EXE
        windowed: 是否隐藏控制台窗口
        clean: 是否清理之前的构建
        upx: 是否使用 UPX 压缩
    """
    if clean:
        clean_build_files()
    
    # 确保 PyInstaller 已安装
    install_pyinstaller()
    
    # 构建命令参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(PROJECT_ROOT),
    ]
    
    # 根据选项添加参数
    if onefile:
        cmd.append("--onefile")
        print("构建模式: 单文件 EXE")
    else:
        cmd.append("--onedir")
        print("构建模式: 文件夹")
    
    if windowed:
        cmd.append("--windowed")
        print("控制台: 隐藏")
    else:
        print("控制台: 显示")
    
    if upx:
        cmd.append("--upx-dir=./upx")
    
    # 添加图标 (如果存在)
    icon_path = PROJECT_ROOT / "assets" / "icon.ico"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
        print(f"图标: {icon_path}")
    
    # 添加版本信息
    version_file = PROJECT_ROOT / "version_info.txt"
    if version_file.exists():
        cmd.extend(["--version-file", str(version_file)])
    
    # 隐藏导入 (可选)
    hidden_imports = [
        "customtkinter",
        "PIL",
        "darkdetect",
        "packaging",
        "websockets",
    ]
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])
    
    # 添加数据文件 (如果需要)
    # cmd.extend(["--add-data", "path/to/assets:assets"])
    
    # 入口点
    cmd.append(str(ENTRY_POINT))
    
    print("\n" + "="*60)
    print("开始构建 EXE 文件...")
    print("="*60)
    print(f"命令: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print("\n" + "="*60)
            print("✓ EXE 文件构建成功!")
            print("="*60)
            if onefile:
                exe_path = DIST_DIR / f"{APP_NAME}.exe"
                print(f"输出位置: {exe_path}")
                if exe_path.exists():
                    size_mb = exe_path.stat().st_size / (1024 * 1024)
                    print(f"文件大小: {size_mb:.2f} MB")
            else:
                print(f"输出位置: {DIST_DIR / APP_NAME}")
            print("\n你现在可以运行生成的 EXE 文件了!")
        else:
            print("\n✗ 构建失败，返回码:", result.returncode)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 构建失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        return False
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ARK: Survival Ascended Server Manager - EXE 打包脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python build_exe.py                    # 默认设置，单文件 exe
  python build_exe.py --onedir           # 生成文件夹格式
  python build_exe.py --clean --onefile  # 清理后重新构建
  python build_exe.py --console          # 显示控制台窗口
        """
    )
    
    parser.add_argument(
        "--onefile",
        action="store_true",
        default=True,
        help="生成单文件 EXE (默认)"
    )
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="生成文件夹格式 (更快的启动速度)"
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="显示控制台窗口"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="清理之前的构建文件"
    )
    parser.add_argument(
        "--no-upx",
        action="store_true",
        help="不使用 UPX 压缩"
    )
    
    args = parser.parse_args()
    
    # 确定是否单文件
    onefile = not args.onedir
    windowed = not args.console
    use_upx = not args.no_upx
    
    # 检查项目结构
    if not ENTRY_POINT.exists():
        print(f"错误: 找不到入口点文件 {ENTRY_POINT}")
        sys.exit(1)
    
    # 执行构建
    success = build_exe(
        onefile=onefile,
        windowed=windowed,
        clean=args.clean,
        upx=use_upx
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
