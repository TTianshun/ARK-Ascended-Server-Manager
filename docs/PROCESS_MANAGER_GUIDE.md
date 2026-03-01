# ProcessManager 多进程管理实现指南

## 概述

ProcessManager 已从单进程管理改造为**字典式多进程管理**，现在支持同时启动和管理多个服务器。

## 主要改变

### API 变更汇总

| 旧 API | 新 API | 说明 |
|--------|--------|------|
| `is_running()` | `is_running(server_id: str)` | 需要传入服务器ID |
| `start(executable, args, cwd)` | `start(server_id, executable, args, cwd)` | 第一个参数是服务器ID |
| `stop(timeout=30)` | `stop(server_id, timeout=30)` | 需要指定停止哪个服务器 |
| `get_pid()` | `get_pid(server_id: str)` | 返回指定服务器的PID |
| ❌ | `get_all_running_servers()` | **新增** - 获取所有运行中的服务器列表 |
| ❌ | `get_running_count()` | **新增** - 获取运行中的服务器数量 |
| ❌ | `stop_all(timeout=30)` | **新增** - 停止所有运行中的服务器 |

## 使用示例

### 1. 基本启动两个不同的服务器

```python
from ark_asa_manager.core import ProcessManager
from pathlib import Path

pm = ProcessManager()

# 启动服务器1
pm.start(
    server_id="island_server",
    executable=Path("C:\\GameServer\\ShooterGameServer.exe"),
    args=["/Map=TheIsland_WP", "?SessionName=Island_PvP", "-server"],
    cwd=Path("C:\\GameServer\\ARK-Survival-Ascended-Server")
)

# 启动服务器2
pm.start(
    server_id="scorched_server",
    executable=Path("C:\\GameServer\\ShooterGameServer.exe"),
    args=["/Map=ScorchedEarth_WP", "?SessionName=Scorched_PvE", "-server"],
    cwd=Path("C:\\GameServer\\ARK-Survival-Ascended-Server")
)

print(f"已启动 {pm.get_running_count()} 个服务器")
```

### 2. 检查和管理运行状态

```python
# 检查特定服务器是否运行中
if pm.is_running("island_server"):
    print(f"Island 服务器运行中，PID: {pm.get_pid('island_server')}")

# 获取所有运行中的服务器
running_servers = pm.get_all_running_servers()
# 输出: ["island_server", "scorched_server"]

# 停止特定服务器
pm.stop("island_server", timeout=30)

# 停止所有服务器
pm.stop_all(timeout=30)
```

## 在 UI (app.py) 中的集成建议

### 场景1: 多个 Server Tab (支持多个活动服务器)

如果 UI 的 ServerTab 需要支持多个同时运行的服务器，建议：

```python
class ServerManagerApp:
    def __init__(self, root, app_base):
        # ... 其他初始化 ...
        self.process_manager = ProcessManager()
        
    def start_server(self, server_name: str) -> None:
        """启动指定的服务器"""
        server_id = self.var_server_profile.get()  # 获取当前选中的服务器配置
        
        # 检查是否已运行
        if self.process_manager.is_running(server_id):
            messagebox.showwarning("警告", f"服务器 {server_id} 已在运行")
            return
        
        try:
            # 构建启动命令
            executable = Path(self.var_server_dir.get()) / "ShooterGameServer.exe"
            args = self._build_start_args(server_id)
            
            # 启动服务器
            if self.process_manager.start(server_id, executable, args=args):
                self.logger.info(f"服务器 {server_id} 启动成功")
                self.var_status.set(f"服务器已启动: {server_id}")
            else:
                messagebox.showerror("错误", f"无法启动服务器 {server_id}")
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {e}")
    
    def stop_server_safe(self, server_name: str) -> None:
        """安全停止指定的服务器"""
        server_id = self.var_server_profile.get()
        
        if not self.process_manager.is_running(server_id):
            messagebox.showinfo("提示", f"服务器 {server_id} 未运行")
            return
        
        try:
            # 可选：在停止前执行 RCON 命令（if RCON available)
            # self.send_rcon_command(server_id, "SaveWorld")
            # self.send_rcon_command(server_id, "DoExit")
            
            if self.process_manager.stop(server_id, timeout=30):
                self.logger.info(f"服务器 {server_id} 已停止")
                self.var_status.set(f"服务器已停止: {server_id}")
            else:
                messagebox.showerror("错误", f"停止服务器 {server_id} 失败")
        except Exception as e:
            messagebox.showerror("错误", f"停止失败: {e}")
    
    def get_server_status(self, server_id: str) -> str:
        """获取服务器状态"""
        if self.process_manager.is_running(server_id):
            pid = self.process_manager.get_pid(server_id)
            return f"运行中 (PID: {pid})"
        else:
            return "已停止"
```

### 场景2: 一次只能运行一个服务器 (当前设计)

如果当前 UI 设计只支持一个活动服务器，但希望保留多进程能力供修改，使用服务器名作为 ID：

```python
def start_server(self) -> None:
    """启动服务器"""
    server_id = self.var_server_profile.get()  # 使用配置名作为 server_id
    
    # 检查是否有其他服务器在运行
    running = self.process_manager.get_all_running_servers()
    if running:
        messagebox.showwarning(
            "警告",
            f"其他服务器仍在运行: {', '.join(running)}\n请先停止它们"
        )
        return
    
    # 启动选中的服务器
    # ... 启动代码 ...
    self.process_manager.start(server_id, ...)
```

### 场景3: 同时列出所有运行中的服务器

在 UI 状态栏或监控面板中显示所有运行中的服务器：

```python
def update_status_display(self) -> None:
    """更新状态显示"""
    running_count = self.process_manager.get_running_count()
    running_servers = self.process_manager.get_all_running_servers()
    
    if running_count == 0:
        status_text = "无服务器运行"
    else:
        status_text = f"运行中: {', '.join(running_servers)} ({running_count}个)"
    
    self.var_status.set(status_text)
```

## 与 RCON 的配合

如果需要对多个服务器执行 RCON 命令，建议为每个服务器创建独立的 RCON 客户端：

```python
class ServerManagerApp:
    def __init__(self, ...):
        # ... 其他初始化 ...
        self.rcon_clients: Dict[str, RCONClient] = {}  # 按 server_id 存储
    
    def connect_rcon(self, server_id: str) -> bool:
        """为指定服务器连接 RCON"""
        if server_id not in self.rcon_clients:
            config = self._get_rcon_config(server_id)
            client = RCONClient(
                host=config.host,
                port=config.port,
                password=config.password
            )
            self.rcon_clients[server_id] = client
        
        return self.rcon_clients[server_id].connect()
    
    def send_rcon_command(self, server_id: str, command: str) -> str:
        """向指定服务器发送 RCON 命令"""
        if server_id in self.rcon_clients:
            return self.rcon_clients[server_id].send_command(command)
        return ""
```

## 向后兼容性

当前使用 ProcessManager 时，所有调用都需要提供 `server_id` 参数。如果需要向后兼容单进程的旧代码，可在 ProcessManager 中添加一个包装器：

```python
class ProcessManager:
    # 用于向后兼容的默认 server_id
    DEFAULT_SERVER_ID = "__default__"
    
    def start_legacy(self, executable: Path, args=None, cwd=None) -> bool:
        """向后兼容的启动方法"""
        return self.start(self.DEFAULT_SERVER_ID, executable, args, cwd)
    
    def stop_legacy(self, timeout: int = 30) -> bool:
        """向后兼容的停止方法"""
        return self.stop(self.DEFAULT_SERVER_ID, timeout)
```

## 测试

查看 `tests/test_process_manager.py` 获取更多测试示例。

运行测试：
```bash
pytest tests/test_process_manager.py -v
```

## 总结

- ✅ ProcessManager 现在支持字典式多进程管理
- ✅ 每个服务器通过 `server_id` (字符串) 唯一标识
- ✅ 支持同时启动和管理多个服务器
- ✅ 添加了新的便利方法（get_all_running_servers, get_running_count, stop_all）
- ✅ 保持简单的 API 接口，易于扩展
