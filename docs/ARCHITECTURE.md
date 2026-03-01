# 项目架构说明文档

## 项目概述

**ARK: Survival Ascended Server Manager** 是一个为Windows平台设计的ARK游戏服务器管理工具，采用现代化的模块化架构。

### 核心特性
- 🛡️ **安全启停**: 确定性启动命令和安全的停止序列
- 📦 **配置管理**: 基于staging-baseline的配置管理工作流
- 🎮 **RCON支持**: 可靠的远程控制和实时监管
- 💾 **自动备份**: 完整的备份和回滚功能
- 📊 **状态监控**: 实时服务器状态和统计信息

---

## 目录结构

```
ARK-Ascended-Server-Manager/
├── src/ark_asa_manager/           # 主包源代码
│   ├── __init__.py                # 包初始化
│   ├── __main__.py                # 应用入口点
│   │
│   ├── ui/                        # 用户界面模块
│   │   ├── __init__.py
│   │   ├── app.py                 # 主应用窗口
│   │   ├── theme.py               # 主题和样式
│   │   └── widgets.py             # 自定义UI组件
│   │
│   ├── core/                      # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── config.py              # 配置文件处理
│   │   ├── storage.py             # 存储区域管理
│   │   ├── process.py             # 进程生命周期
│   │   └── server.py              # 服务器业务逻辑
│   │
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   ├── server.py              # 服务器配置和状态
│   │   └── enums.py               # 枚举定义
│   │
│   ├── rcon/                      # RCON客户端
│   │   ├── __init__.py
│   │   ├── client.py              # RCON客户端接口
│   │   └── protocol.py            # RCON协议实现
│   │
│   ├── ini/                       # INI文件处理
│   │   ├── __init__.py
│   │   ├── parser.py              # INI解析器
│   │   └── writer.py              # INI写入器
│   │
│   ├── steam/                     # Steam集成
│   │   ├── __init__.py
│   │   └── manager.py             # SteamCMD管理
│   │
│   └── utils/                     # 工具函数
│       ├── __init__.py
│       ├── constants.py           # 全局常量
│       ├── logger.py              # 日志系统
│       ├── windows.py             # Windows操作
│       └── downloader.py          # 文件下载
│
├── tests/                         # 测试套件
│   ├── __init__.py
│   ├── test_basic.py
│   ├── tests_ini.py
│   └── test_rcon.py
│
├── docs/                          # 文档
│   ├── img/                       # 截图和图片
│   ├── ARCHITECTURE.md            # 本文件
│   ├── DEVELOPMENT.md             # 开发指南
│   └── API.md                     # API文档
│
├── assets/                        # 资源文件
│   ├── icons/
│   └── images/
│
├── legacy/                        # 遗留代码
│   └── powershell/                # 旧版PowerShell脚本
│
├── pyproject.toml                 # 项目配置
├── requirements.txt               # 依赖列表
├── .gitignore                     # Git忽略规则
├── README.md                      # 项目说明
└── LICENSE                        # 许可证
```

---

## 关键模块详解

### 1. UI Module (`ui/`)
负责用户界面和交互。

**主要类**:
- `ServerManagerApp`: 主应用窗口
- 主题和样式配置函数

**职责**:
- 创建和管理窗口
- 处理用户事件
- 更新界面显示

```python
from ark_asa_manager.ui import ServerManagerApp
app = ServerManagerApp(root, app_base_path)
```

### 2. Core Module (`core/`)
包含核心业务逻辑。

#### ConfigManager
管理应用和服务器配置。

```python
from ark_asa_manager.core import ConfigManager
from pathlib import Path

config = ConfigManager(Path("~/.ark-manager"))
config.set("server_dir", "/path/to/server")
config.save()
```

#### StorageManager
管理存储区域结构（staging、baseline、backup等）。

```python
from ark_asa_manager.core import StorageManager

storage = StorageManager(app_base)
staging = storage.get_staging_dir("MyServer")
baseline = storage.get_baseline_dir("MyServer")
backups = storage.get_backup_dir("MyServer")
```

#### ProcessManager
管理多个服务器进程的启动、停止和状态监控。支持同时运行多个服务器。

```python
from ark_asa_manager.core import ProcessManager
from pathlib import Path

pm = ProcessManager()

# 启动服务器1
pm.start("server1", Path("ShooterGameServer.exe"), args=["ServerParams"])
print(f"Server1 PID: {pm.get_pid('server1')}")

# 启动服务器2
pm.start("server2", Path("ShooterGameServer.exe"), args=["ServerParams"])
print(f"Server2 PID: {pm.get_pid('server2')}")

# 检查运行中的服务器
running = pm.get_all_running_servers()
print(f"运行中的服务器: {running}")
print(f"运行数量: {pm.get_running_count()}")

# 停止特定服务器
pm.stop("server1", timeout=30)

# 停止所有服务器
pm.stop_all(timeout=30)
```

### 3. Models Module (`models/`)
定义数据结构和枚举。

```python
from ark_asa_manager.models import ServerConfig, ServerStatus

config = ServerConfig(
    name="MyServer",
    server_dir=Path("C:\\GameServer\\ARK-Server"),
    port=7777,
    max_players=70,
)
```

### 4. RCON Module (`rcon/`)
处理与服务器的远程控制通信。

```python
from ark_asa_manager.rcon import RCONClient

rcon = RCONClient(host="127.0.0.1", port=27020, password="admin")
if rcon.connect():
    players = rcon.get_players()
    rcon.save()
    rcon.disconnect()
```

### 5. INI Module (`ini/`)
处理ARK服务器配置文件。

```python
from ark_asa_manager.ini import INIParser
from pathlib import Path

parser = INIParser()
parser.parse_file(Path("GameUserSettings.ini"))

# 读取配置
difficulty = parser.get("ServerSettings", "DifficultyOffset")

# 修改配置
parser.set("ServerSettings", "MaxPlayers", "100")

# 保存
parser.save_file(Path("GameUserSettings.ini"))
```

### 6. Steam Module (`steam/`)
处理SteamCMD集成。

```python
from ark_asa_manager.steam import SteamManager

steam = SteamManager(Path("C:\\GameServer\\SteamCMD"))
if not steam.is_installed():
    steam.install("https://...")

steam.update_app(2430930, Path("C:\\GameServer\\ARK"))
```

### 7. Utils Module (`utils/`)
提供各种工具函数。

```python
from ark_asa_manager.utils import (
    setup_logger,
    get_logger,
    constants,
)

# 日志
setup_logger(log_dir)
logger = get_logger(__name__)

# 常量
from ark_asa_manager.utils.constants import (
    APP_NAME,
    DEFAULT_RCON_PORT,
    MAP_PRESETS,
)
```

---

## 数据流

### 服务器启动流程
```
用户点击启动
    ↓
ConfigManager 加载配置
    ↓
StorageManager 准备staging目录
    ↓
INIParser 应用配置更改
    ↓
ProcessManager 启动服务器进程
    ↓
RCONClient 连接并验证
    ↓
UI 更新状态为 RUNNING
```

### 配置修改流程
```
用户编辑INI
    ↓
INIParser 解析变更
    ↓
ConfigManager 保存到配置文件
    ↓
StorageManager 在启动时应用更改
    ↓
baseline 用于安全回滚
```

---

## 依赖关系

```
ui/
    └── core/, models/, utils/, rcon/

core/
    └── models/, utils/

rcon/
    └── (无依赖)

ini/
    └── (无依赖)

steam/
    └── utils/
```

---

## 配置管理策略

### Staging (暂存)
- 用户编辑的临时配置区域
- 在服务器启动时应用到生产环境

### Baseline (基线)
- 服务器初始化时的原始配置副本
- 用于安全回滚和版本对比

### 优势
- ✅ 避免半应用配置问题
- ✅ 支持配置版本控制
- ✅ 实现安全回滚
- ✅ 离线编辑支持

---

## 扩展指南

### 添加新的管理功能

1. **在models中定义数据模型**
   ```python
   @dataclass
   class MyFeature:
       # 定义字段
   ```

2. **在core中实现业务逻辑**
   ```python
   class MyFeatureManager:
       def __init__(self, storage: StorageManager):
           # 初始化
   ```

3. **在UI中添加界面**
   ```python
   # 在ui/app.py或新的ui/feature.py中添加
   ```

### 添加新的命令行工具

编辑 `pyproject.toml`:
```toml
[project.scripts]
my-tool = "ark_asa_manager.tools.my_tool:main"
```

---

## 开发最佳实践

1. **类型注解**: 使用类型提示提高代码可维护性
2. **日志记录**: 使用get_logger()而不是print()
3. **异常处理**: 使用try-except并记录错误
4. **文档**: 为公共API添加docstring
5. **测试**: 在tests/中添加单元测试

---

## 版本号管理

遵循 [Semantic Versioning](https://semver.org/):
- MAJOR: 破坏性更改
- MINOR: 新功能（向后兼容）
- PATCH: 错误修复

---

## 相关链接

- [开发指南](./DEVELOPMENT.md)
- [API文档](./API.md)
- [project README](../README.md)
