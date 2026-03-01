#!/bin/bash
# ARK: Survival Ascended Server Manager - EXE 打包脚本 (Linux/Mac)
# 这个脚本会调用 Python 打包脚本，用于在 WSL 或 Linux/Mac 上构建

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "======================================"
echo "ARK Ascended Server Manager - EXE 打包"
echo "======================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 找不到 Python3${NC}"
    echo "请确保已安装 Python 3.10 或更高版本"
    exit 1
fi

python3 --version

# 检查系统
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    echo "检测到 Windows 系统，建议使用 build_exe.bat"
fi

# 显示菜单
echo ""
echo "选择打包方式:"
echo "1. 单文件 EXE (推荐) [默认]"
echo "2. 文件夹格式 (启动快)"
echo "3. 单文件 EXE + 清理旧文件"
echo "4. 帮助"
echo "5. 退出"
echo ""

read -p "请选择 (默认选1): " choice
choice=${choice:-1}

case $choice in
    1)
        echo -e "${YELLOW}构建单文件 EXE...${NC}"
        python3 build_exe.py --onefile
        ;;
    2)
        echo -e "${YELLOW}构建文件夹格式...${NC}"
        python3 build_exe.py --onedir
        ;;
    3)
        echo -e "${YELLOW}清理旧文件并构建单文件 EXE...${NC}"
        python3 build_exe.py --onefile --clean
        ;;
    4)
        python3 build_exe.py --help
        ;;
    5)
        echo "已退出"
        exit 0
        ;;
    *)
        echo -e "${RED}无效选择${NC}"
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}构建完成！${NC}"
    echo "输出文件位置: $SCRIPT_DIR/dist"
else
    echo ""
    echo -e "${RED}构建失败！${NC}"
    exit 1
fi
