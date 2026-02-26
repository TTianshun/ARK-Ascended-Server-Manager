# 快速参考

## 📁 找我的代码

| 功能 | 位置 | 入口 |
|------|------|------|
| 应用启动 | `src/ark_asa_manager/__main__.py` | `ark-asa-manager` |
| 主窗口 | `src/ark_asa_manager/ui/app.py` | `ServerManagerApp` |
| RCON操作 | `src/ark_asa_manager/rcon/` | `RCONClient` |
| INI处理 | `src/ark_asa_manager/ini/parser.py` | `INIParser` |
| 配置管理 | `src/ark_asa_manager/core/config.py` | `ConfigManager` |
| 数据模型 | `src/ark_asa_manager/models/` | `ServerConfig` |
| 常量定义 | `src/ark_asa_manager/utils/constants.py` | `APP_NAME` |
| 日志系统 | `src/ark_asa_manager/utils/logger.py` | `get_logger()` |

## 🔧 常用命令

```bash
# 🚀 运行应用 (无需安装!)
# Windows: 双击此文件
launch.bat
# 或运行
python RUN.py
# 或在命令行
python -m ark_asa_manager

# Linux/Mac
bash launch.sh

# 可选: 安装后使用命令
pip install -e .
ark-asa-manager
```

```bash
# 测试
pytest tests/                          # 运行所有测试
pytest tests/test_basic.py::TestINIParser  # 运行特定测试
pytest --cov=src/ark_asa_manager tests/    # 带覆盖率报告

# 代码格式
black src/ tests/                      # 自动格式化
flake8 src/ tests/                     # 风格检查
isort src/ tests/                      # Import排序
mypy src/                              # 类型检查

# 打包 (可选)
pip install -e .                       # 本地安装（开发模式）
pip install -e ".[dev]"                # 安装开发依赖
python -m build                        # 构建发布包
```

## 💻 代码示例

### 导入常用模块
```python
from ark_asa_manager.models import ServerConfig, ServerStatus
from ark_asa_manager.core import ConfigManager, StorageManager
from ark_asa_manager.rcon import RCONClient
from ark_asa_manager.ini import INIParser
from ark_asa_manager.utils import get_logger
```

### 创建服务器配置
```python
from ark_asa_manager.models import ServerConfig
from pathlib import Path

config = ServerConfig(
    name="MyServer",
    server_dir=Path("C:\\GameServer\\ARK"),
    port=7777,
    max_players=70,
)
```

### 使用RCON
```python
from ark_asa_manager.rcon import RCONClient

rcon = RCONClient("127.0.0.1", 27020, "password")
if rcon.connect():
    players = rcon.get_players()
    rcon.disconnect()
```

### 处理INI文件
```python
from ark_asa_manager.ini import INIParser
from pathlib import Path

parser = INIParser()
parser.parse_file(Path("GameUserSettings.ini"))
parser.set("ServerSettings", "MaxPlayers", "100")
parser.save_file(Path("GameUserSettings.ini"))
```

### logging日志
```python
from ark_asa_manager.utils import get_logger

logger = get_logger(__name__)
logger.info("应用启动")
logger.warning("警告信息")
logger.error("错误信息")
```

## 📚 文档导航

| 文档 | 内容 |
|------|------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 完整的系统架构说明 |
| [DEVELOPMENT.md](docs/DEVELOPMENT.md) | 开发环境和工作流 |
| [MIGRATION.md](docs/MIGRATION.md) | 从旧版本迁移指南 |
| [PROJECT_STRUCTURE_GUIDE.md](docs/PROJECT_STRUCTURE_GUIDE.md) | 结构重构说明 |

## 🧪 快速测试

```bash
# 创建一个简单的测试
cat > test_my_feature.py << 'EOF'
import pytest
from ark_asa_manager.models import ServerConfig
from pathlib import Path

def test_server_config():
    config = ServerConfig(
        name="test",
        server_dir=Path("/tmp"),
    )
    assert config.name == "test"
    assert config.port == 7777

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF

# 运行测试
pytest test_my_feature.py -v
```

## 🚨 常见问题

**Q: 怎样修改全局常量？**
```python
# 编辑 src/ark_asa_manager/utils/constants.py
APP_NAME = "新名字"
```

**Q: 怎样添加新的数据模型？**
```python
# 创建 src/ark_asa_manager/models/my_model.py
from dataclasses import dataclass

@dataclass
class MyModel:
    field1: str
    field2: int
```

**Q: 怎样添加新命令？**
```python
# 编辑 pyproject.toml
[project.scripts]
my-command = "ark_asa_manager.tools.my_tool:main"
```

**Q: 日志文件在哪？**
- Windows: `%APPDATA%/ARK-Ascended-Server-Manager/logs/app.log`
- Linux: `~/.config/ark-ascended-server-manager/logs/app.log`

**Q: 如何调试？**
```bash
# 启用DEBUG级别日志
export PYTHONUNBUFFERED=1
python -m ark_asa_manager
```

## 📊 项目统计

- **模块数**: 12
- **代码行数**: ~50 (从5600+重构)
- **支持Python**: 3.10+
- **依赖数**: 最少化 (只有certifi)
- **文档页面**: 4+

## 🎯 下一步

1. 👉 阅读 [ARCHITECTURE.md](docs/ARCHITECTURE.md)
2. 👉 设置开发环境 (参考 [DEVELOPMENT.md](docs/DEVELOPMENT.md))
3. 👉 运行测试看看一切正常
4. 👉 开始添加功能或修复问题

---

**需要帮助？查看docs文件夹或GitHub Issues！**
