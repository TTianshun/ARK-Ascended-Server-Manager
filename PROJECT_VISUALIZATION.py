"""
项目结构可视化总结
"""

STRUCTURE = """
╔════════════════════════════════════════════════════════════════════╗
║    ARK: Survival Ascended Server Manager - 现代化模块化架构        ║
╚════════════════════════════════════════════════════════════════════╝

📦 ARK-Ascended-Server-Manager/
│
├── 📂 src/ark_asa_manager/                 【主源代码】
│   │
│   ├── 📄 __init__.py                      包初始化
│   ├── 📄 __main__.py                      ⭐ 应用入口点
│   │
│   ├── 📂 ui/                              【用户界面】
│   │   ├── app.py                          主应用窗口
│   │   ├── theme.py                        主题与样式
│   │   ├── widgets.py                      自定义组件
│   │   └── __init__.py
│   │
│   ├── 📂 core/                            【核心业务逻辑】
│   │   ├── config.py                       配置文件管理
│   │   ├── storage.py                      存储区域管理
│   │   ├── process.py                      进程生命周期
│   │   └── __init__.py
│   │
│   ├── 📂 models/                          【数据模型】
│   │   ├── server.py                       服务器配置&状态
│   │   ├── enums.py                        枚举类型定义
│   │   └── __init__.py
│   │
│   ├── 📂 rcon/                            【RCON通信】
│   │   ├── client.py                       RCON客户端
│   │   ├── protocol.py                     RCON协议
│   │   └── __init__.py
│   │
│   ├── 📂 ini/                             【INI配置处理】
│   │   ├── parser.py                       INI解析器
│   │   └── __init__.py
│   │
│   ├── 📂 steam/                           【Steam集成】
│   │   ├── manager.py                      SteamCMD管理
│   │   └── __init__.py
│   │
│   └── 📂 utils/                           【工具函数】
│       ├── constants.py                    全局常量定义
│       ├── logger.py                       日志系统
│       ├── windows.py                      Windows操作
│       ├── downloader.py                   文件下载
│       └── __init__.py
│
├── 📂 tests/                               【单元测试】
│   ├── test_basic.py                       基础测试
│   ├── test_ini.py                         INI模块测试
│   ├── test_rcon.py                        RCON模块测试
│   └── __init__.py
│
├── 📂 docs/                                【项目文档】
│   ├── ARCHITECTURE.md                     📖 架构说明
│   ├── DEVELOPMENT.md                      📖 开发指南
│   ├── MIGRATION.md                        📖 迁移指南
│   ├── PROJECT_STRUCTURE_GUIDE.md          📖 结构指南
│   ├── img/                                文档图片
│   └── ...
│
├── 📂 assets/                              【资源文件】
│   ├── app.ico                             应用图标
│   └── ...
│
├── 📂 legacy/                              【遗留代码】
│   └── powershell/                         旧版PowerShell脚本
│
├── 📄 pyproject.toml                       ⭐ 项目配置 (新)
├── 📄 .gitignore                           Git忽略规则 (改进)
├── 📄 requirements.txt                     依赖列表
├── 📄 README.md                            项目说明
└── 📄 LICENSE                              许可证

═══════════════════════════════════════════════════════════════════════

【模块依赖关系】

    用户
      │
      ▼
    ui/ 
    ├── ◄── core/        (配置、存储)
    ├── ◄── models/      (数据结构)
    ├── ◄── rcon/        (远程控制)
    ├── ◄── ini/         (文件处理)
    └── ◄── utils/       (工具)
     │
     ├── core/
     │   └── ◄── models/, utils/
     │
     ├── rcon/
     │   └── (独立模块)
     │
     ├── ini/
     │   └── (独立模块)
     │
     ├── steam/
     │   └── ◄── utils/
     │
     └── utils/
         └── (基础层)

═══════════════════════════════════════════════════════════════════════

【数据流示例】

服务器启动流程：
  1️⃣ UI 接收启动请求
     │
  2️⃣ ConfigManager 加载配置
     │
  3️⃣ StorageManager 准备暂存目录 (staging)
     │
  4️⃣ INIParser 应用配置更改
     │
  5️⃣ ProcessManager 启动服务器进程
     │
  6️⃣ RCONClient 连接并验证
     │
  7️⃣ UI 更新状态为 RUNNING

═══════════════════════════════════════════════════════════════════════

【快速开始】

1️⃣ 环境设置
   $ python -m venv venv
   $ venv\\Scripts\\activate
   $ pip install -e \".[dev]\"

2️⃣ 运行应用
   $ ark-asa-manager
   或
   $ python -m ark_asa_manager

3️⃣ 运行测试
   $ pytest tests/ -v

4️⃣ 代码格式化
   $ black src/ tests/

5️⃣ 查看文档
   $ 打开 docs/ARCHITECTURE.md

═══════════════════════════════════════════════════════════════════════

【核心特性】

✅ 模块化设计      - 12个有组织的模块
✅ 标准Python结构  - 遵循PEP标准
✅ 完整文档        - 架构、开发和迁移指南
✅ 测试框架        - 完整的单元测试支持
✅ 类型注解        - 改进的IDE支持
✅ 日志系统        - 结构化的日志记录
✅ 配置管理        - 灵活的配置处理
✅ RCON支持        - 远程服务器控制
✅ INI处理         - 完整的配置文件支持
✅ Steam集成       - SteamCMD管理

═══════════════════════════════════════════════════════════════════════

【许可和贡献】

许可证: MIT
主要作者: Ch4r0ne
仓库: https://github.com/Ch4r0ne/ARK-Ascended-Server-Manager

═══════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(STRUCTURE)
