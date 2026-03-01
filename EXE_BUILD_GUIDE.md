# EXE 打包指南

本指南说明如何将 ARK Ascended Server Manager 打包成 Windows EXE 文件。

## 快速开始

### 方法 1: 使用批处理脚本（推荐 Windows 用户）

1. **双击运行打包脚本**：
   ```
   双击 build_exe.bat
   ```

2. **选择打包方式**：
   - 选择 `1` - 单文件 EXE（推荐，文件更小）
   - 选择 `2` - 文件夹格式（启动更快）

3. **等待完成**：脚本会自动打开 `dist` 文件夹，你会看到生成的 EXE 文件

### 方法 2: 使用 Python 脚本

如果你是开发者或需要更多控制，可以直接运行 Python 脚本：

```bash
cd d:\Dev\ARK-Ascended-Server-Manager

# 安装打包依赖
pip install -r requirements-build.txt

# 生成单文件 EXE (推荐)
python build_exe.py --onefile

# 或生成文件夹格式
python build_exe.py --onedir

# 清理旧构建后重新生成
python build_exe.py --onefile --clean
```

### 方法 3: 在 PowerShell 中运行（高级用户）

```powershell
cd d:\Dev\ARK-Ascended-Server-Manager
.\build_exe.bat
```

## 打包选项详解

| 选项 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| `--onefile` | 生成单个 EXE 文件 | 易于分发、清洁 | 启动速度稍慢 |
| `--onedir` | 生成文件夹（含依赖） | 启动速度快 | 文件多、难以分发 |
| `--windowed` | 隐藏控制台窗口（默认） | 更美观 | - |
| `--console` | 显示控制台窗口 | 便于调试 | 不适合发布 |
| `--clean` | 清理旧的构建文件 | 节省空间、避免冲突 | 耗时更长 |

## 文件说明

### 生成的文件

```
dist/
├── ARK-Ascended-Server-Manager.exe    # 单文件 EXE (--onefile 时)
└── ARK-Ascended-Server-Manager/       # 文件夹 (--onedir 时)
    ├── ARK-Ascended-Server-Manager.exe
    ├── customtkinter/
    ├── PIL/
    └── ...其他依赖文件...

build/                                  # 构建临时文件（可删除）
ARK-Ascended-Server-Manager.spec        # PyInstaller 规范文件
```

## 常见问题

### Q1: 生成的 EXE 很大（>100MB）

这是正常的，因为包含了所有依赖。你可以：
- 使用 `--onedir` 格式，可以稍微压缩
- 使用 UPX 压缩工具进一步压缩（需要单独安装）

### Q2: EXE 无法启动

可能的原因：
1. 缺少依赖 - 检查 `requirements.txt` 是否安装完整
2. Python 路径问题 - 确保虚拟环境激活
3. 权限问题 - 以管理员身份运行

### Q3: 如何添加应用图标

1. 将图标文件放在 `assets/icon.ico`
2. 重新运行打包脚本，图标会自动应用

### Q4: 构建失败

检查以下步骤：

```powershell
# 1. 检查 Python 版本
python --version  # 应该是 3.10 或更高

# 2. 检查依赖是否安装
pip list | findstr "PyInstaller"

# 3. 手动安装依赖
pip install -r requirements.txt
pip install -r requirements-build.txt

# 4. 清理并重新构建
python build_exe.py --onefile --clean
```

## 发布 EXE

### 单文件格式 (推荐)

```bash
# 生成
python build_exe.py --onefile

# 分发
dist/ARK-Ascended-Server-Manager.exe  # 直接发送这个文件即可
```

### 文件夹格式

```bash
# 生成
python build_exe.py --onedir

# 分发
复制整个 dist/ARK-Ascended-Server-Manager/ 文件夹
```

## 高级配置

### 自定义 PyInstaller 参数

编辑 `build_exe.py` 中的以下部分：

```python
# 添加隐藏导入
hidden_imports = [
    "customtkinter",
    "PIL",
    "darkdetect",
    "packaging",
]

# 添加数据文件
# cmd.extend(["--add-data", "assets:assets"])
```

### 使用 UPX 压缩

1. 下载 UPX：https://upx.github.io/
2. 解压到项目目录的 `upx/` 文件夹
3. 运行：`python build_exe.py --onefile`（自动使用 UPX）

## 针对不同场景的推荐

### 场景 1: 个人使用
```bash
python build_exe.py --onefile
# 优点：单文件，易于携带
```

### 场景 2: 广泛分发
```bash
python build_exe.py --onefile --clean
# 生成最干净的单文件，适合在网站上发布
```

### 场景 3: 便携版
```bash
python build_exe.py --onedir
# 优点：启动快，便于快速迭代
```

## 杀毒软件误报

某些杀毒软件可能会误报 PyInstaller 生成的 EXE。这是正常现象。

如果需要消除警告，可以：
1. 对 EXE 进行数字签名（需要 Windows 证书）
2. 提交到 VirusTotal 进行验证
3. 上传到杀毒软件的误报反馈系统

## 批量生成

需要为多个配置生成 EXE？

```bash
# 生成所有版本
python build_exe.py --onefile --clean
python build_exe.py --onedir --clean
```

## 故障排除

如果遇到问题，收集以下信息：

```bash
# 1. 获取完整错误日志
python build_exe.py --onefile 2>&1 | tee build.log

# 2. 检查环境
python --version
pip --version
pip list

# 3. 检查项目文件
dir src\ark_asa_manager
```

## 更多帮助

查看完整帮助：
```bash
python build_exe.py --help
```

## 下一步

生成 EXE 后：

1. **测试** - 在干净的 Windows 系统上测试 EXE
2. **发布** - 上传到 GitHub Releases
3. **文档** - 更新 README，说明下载和使用说明
4. **监控** - 收集用户反馈，持续改进

---

祝你打包愉快！ 🎮
