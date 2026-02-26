# 🚀 应用启动指南

**重要: 不需要任何安装!** 

## 最简单的方式

### Windows
```bash
# 方式1: 直接双击 (最推荐 ✨)
launch.bat

# 方式2: 运行Python脚本
python RUN.py

# 方式3: 使用命令行
python -m ark_asa_manager
```

### Linux / macOS
```bash
# 方式1: 运行Shell脚本
bash launch.sh

# 方式2: 使用命令行
python -m ark_asa_manager
```

### 前置条件
- Python 3.10 或更高版本
- 已安装Python的tkinter (通常自带)

---

## 验证Python安装

```bash
# 检查Python版本
python --version

# 检查tkinter可用性
python -c "import tkinter; print('tkinter OK')"
```

---

## 可选: 安装为命令行工具

如果你想随处使用 `ark-asa-manager` 命令:

```bash
# 一次性安装 (开发模式)
pip install -e .

# 然后即可使用
ark-asa-manager
```

---

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| `ModuleNotFoundError` | 确保在项目根目录运行 |
| Python未找到 | 将Python添加到PATH或使用完整路径 |
| tkinter错误 | `pip install tk-tools` 或使用系统包管理器安装 |
| 权限拒绝 | Windows上以管理员身份运行 |

---

## 不同场景的启动

**新手用户**:
```bash
# Windows: 直接双击 launch.bat
# Linux/Mac: bash launch.sh
```

**开发者**:
```bash
python -m ark_asa_manager
# 或在IDE中运行 __main__.py
```

**生产环境**:
```bash
pip install -e .
ark-asa-manager
```

---

## 技术细节

应用使用以下启动流程:

```
1. launch.bat/RUN.py → 执行 python -m ark_asa_manager
2. __main__.py → 调用 launch() 函数
3. launch() → 初始化日志、创建UI、启动事件循环
```

所有启动方式都是等价的，只是便利程度不同。

---

**选择你最喜欢的方式开始吧! 🎮**
