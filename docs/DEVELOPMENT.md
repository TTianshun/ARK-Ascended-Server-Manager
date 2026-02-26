# 开发指南

## 环境设置

### 前置条件
- Python 3.10 或更高版本
- pip 或 conda

### 克隆并设置虚拟环境

```bash
# 克隆仓库
git clone https://github.com/Ch4r0ne/ARK-Ascended-Server-Manager.git
cd ARK-Ascended-Server-Manager

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\\Scripts\\activate
# Linux/Mac:
source venv/bin/activate

# 安装开发版本
pip install -e \".[dev]\"
```

## 运行应用

### 使用命令行
```bash
ark-asa-manager
```

### 直接运行模块
```bash
python -m ark_asa_manager
```

### 开发调试
```bash
# 启用详细日志
PYTHONUNBUFFERED=1 python -m ark_asa_manager
```

## 测试

### 运行所有测试
```bash
pytest tests/
```

### 运行特定测试
```bash
pytest tests/test_basic.py::TestINIParser
```

### 查看覆盖率报告
```bash
pytest --cov=src/ark_asa_manager tests/
# 或
pytest --cov=src/ark_asa_manager --cov-report=html tests/
# 打开htmlcov/index.html查看详细报告
```

## 代码质量

### 代码格式化（Black）
```bash
black src/ tests/
```

### Import排序（isort）
```bash
isort src/ tests/
```

### 代码检查（Flake8）
```bash
flake8 src/ tests/
```

### 类型检查（mypy）
```bash
mypy src/
```

### 一键检查
```bash
# 创建脚本或使用make
black src/ tests/ && isort src/ tests/ && flake8 src/ tests/
```

## 项目结构导航

```
src/ark_asa_manager/
src/ark_asa_manager/
├── ui/           # 用户界面组件
├── core/         # 业务逻辑
├── models/       # 数据模型
├── rcon/         # RCON通信
├── ini/          # 配置文件处理
├── steam/        # Steam集成
└── utils/        # 工具函数
```

## 常见开发任务

### 添加新功能

1. 在models中定义数据模型
2. 在core中实现业务逻辑
3. 在ui中添加用户界面
4. 在tests中添加单元测试
5. 更新docs文档

### 示例：添加新的管理功能

1. **创建数据模型** (`models/my_feature.py`):
```python
from dataclasses import dataclass

@dataclass
class MyFeature:
    name: str
    value: int
```

2. **实现业务逻辑** (`core/my_feature_manager.py`):
```python
class MyFeatureManager:
    def __init__(self, storage):
        self.storage = storage
    
    def create(self, feature: MyFeature):
        # 实现
```

3. **添加UI** (`ui/my_feature_panel.py`):
```python
import tkinter as tk

class MyFeaturePanel(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # 创建UI
```

4. **添加测试** (`tests/test_my_feature.py`):
```python
def test_my_feature():
    # 测试实现
```

## 调试技巧

### 启用详细日志
编辑 `__main__.py`:
```python
setup_logger(log_dir, level=logging.DEBUG)
```

### 打印到日志
```python
from ark_asa_manager.utils import get_logger

logger = get_logger(__name__)
logger.debug(f"调试信息: {value}")
logger.info(f"信息: {value}")
logger.warning(f"警告: {value}")
logger.error(f"错误: {value}")
```

### 快速调试某个模块
```python
# 在模块末尾添加
if __name__ == "__main__":
    # 测试代码
    pass
```

## 提交代码

### 提交前检查清单
- [ ] 代码遵循 Black 格式
- [ ] 所有测试通过
- [ ] 类型检查（mypy）无错误
- [ ] 代码覆盖率 > 80%
- [ ] 更新相关文档
- [ ] 编写清晰的提交信息

### 提交信息格式
```
feat: 添加新功能
fix: 修复某个问题
docs: 更新文档
test: 添加测试
refactor: 代码重构
```

## 性能优化

### 分析性能
```bash
python -m cProfile -s cumulative -m ark_asa_manager
```

### 内存分析
```bash
pip install memory_profiler
python -m memory_profiler __main__.py
```

## 文档编写

### API文档
使用Google风格的docstring:
```python
def my_function(arg1: str, arg2: int) -> bool:
    \"\"\"简短描述。
    
    更详细的描述。
    
    Args:
        arg1: 参数说明
        arg2: 参数说明
    
    Returns:
        返回值说明
    
    Raises:
        ValueError: 异常说明
    \"\"\"
```

## 常见问题

### 导入错误
确保安装了包：
```bash
pip install -e .
```

### 权限错误
Windows上确保以管理员身份运行。

### 日志文件位置
在 `%APPDATA%/ARK-Ascended-Server-Manager/logs/` 中

## 有用的资源

- [Python 3.10 文档](https://docs.python.org/3.10/)
- [tkinter 文档](https://docs.python.org/3/library/tkinter.html)
- [pytest 文档](https://docs.pytest.org/)
- [ARK 官方文档](https://ark.wiki.gg/)
