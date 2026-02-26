# 项目重构迁移指南

## 什么改变了？

### 之前（单体结构）
```
ARK-Ascended-Server-Manager.py (5600+ 行单文件)
├── 常量定义
├── 数据模型
├── UI逻辑 (tkinter)
├── RCON客户端
├── INI处理
├── 进程管理
├── 配置管理
└── 工具函数
```

**问题**:
- ❌ 代码难以维护
- ❌ 单元测试困难
- ❌ 功能复用困难
- ❌ 新开发者难以上手

### 现在（模块化结构）
```
src/ark_asa_manager/
├── ui/                # 用户界面
├── core/              # 核心业务逻辑
├── models/            # 数据模型
├── rcon/              # RCON通信
├── ini/               # 配置处理
├── steam/             # Steam集成
├── utils/             # 工具函数
tests/                 # 单元测试
docs/                  # 详细文档
```

**优势**:
- ✅ 代码模块化，结构清晰
- ✅ 便于单元测试
- ✅ 功能容易复用
- ✅ 新开发者快速上手
- ✅ 便于维护和扩展

---

## 迁移步骤

### 1. 备份原始文件
```bash
git add .
git commit -m "Backup: Original monolithic structure"
```

### 2. 环境设置
```bash
# 删除旧的虚拟环境（可选）
rmdir /s venv

# 创建新的虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -e ".[dev]"
```

### 3. 新的运行方式

**之前**:
```bash
python ARK-Ascended-Server-Manager.py
```

**现在** (三种方式):
```bash
# 方式1: 使用命令行工具
ark-asa-manager

# 方式2: 直接运行模块
python -m ark_asa_manager

# 方式3: 进入虚拟环境后运行
cd src
python -m ark_asa_manager
```

---

## 代码迁移映射表

### 常量定义

**之前** (`ARK-Ascended-Server-Manager.py`):
```python
APP_NAME = "ARK: Survival Ascended Server Manager"
DEFAULT_PORT = 7777
```

**现在** (`src/ark_asa_manager/utils/constants.py`):
```python
from ark_asa_manager.utils.constants import (
    APP_NAME,
    DEFAULT_PORT,
)
```

### 数据模型

**之前**:
```python
@dataclass
class ServerConfig:
    # ...
```

**现在**:
```python
from ark_asa_manager.models import ServerConfig
```

### RCON操作

**之前**:
```python
class RCONClient:
    # 5600行中的一部分
```

**现在**:
```python
from ark_asa_manager.rcon import RCONClient

rcon = RCONClient("127.0.0.1", 27020, "password")
rcon.connect()
rcon.execute("ListPlayers")
```

### INI处理

**之前**:
```python
def read_ini(path):
    # 实现
    
def write_ini(path, data):
    # 实现
```

**现在**:
```python
from ark_asa_manager.ini import INIParser

parser = INIParser()
parser.parse_file(path)
parser.set("Section", "Key", "Value")
parser.save_file(path)
```

### 配置管理

**之前**:
```python
with open("config.json") as f:
    config = json.load(f)
```

**现在**:
```python
from ark_asa_manager.core import ConfigManager

config_mgr = ConfigManager(app_base)
value = config_mgr.get("key")
config_mgr.set("key", value)
config_mgr.save()
```

---

## UI重构进度

### 第一阶段（已完成）
- ✅ 项目结构
- ✅ 核心模块
- ✅ 数据模型
- ✅ 基础框架

### 第二阶段（即将进行）
- ⏳ 迁移UI组件
- ⏳ 实现主窗口
- ⏳ 实现各个功能面板
- ⏳ 集成核心逻辑

### 第三阶段（计划中）
- 📋 完整测试
- 📋 性能优化
- 📋 用户文档
- 📋 发布新版本

---

## 兼容性

### 向后兼容
- 保留 `legacy/` 目录中的旧PowerShell脚本
- 配置文件格式保持不变

### 迁移注意事项
1. 新的应用数据目录: `%APPDATA%/ARK-Ascended-Server-Manager/`
2. 日志位置: `%APPDATA%/ARK-Ascended-Server-Manager/logs/`
3. 需要重新配置服务器路径和RCON设置

---

## 常见问题

### Q: 旧的配置文件还能用吗？
**A**: 目前的重构是基础结构调整。配置迁移工具会在第二阶段实现。

### Q: 能同时运行旧版本和新版本吗？
**A**: 可以，但建议备份原始文件后再迁移。

### Q: 如何报告兼容性问题？
**A**: 在GitHub中创建Issue并附加详细信息。

---

## 下一步

1. **对现有功能进行单元测试** (tests/)
2. **逐步迁移UI代码** (ui/)
3. **添加新的管理功能**
4. **性能优化**
5. **用户测试和反馈**

---

## 支持和反馈

有问题或建议？请：
1. 查看 [DEVELOPMENT.md](./DEVELOPMENT.md) 了解开发指南
2. 查看 [ARCHITECTURE.md](./ARCHITECTURE.md) 了解架构细节
3. 在GitHub创建Issue或Discussion

