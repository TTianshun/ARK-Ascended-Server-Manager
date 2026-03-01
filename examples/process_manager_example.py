"""
ProcessManager 多进程管理 - 使用示例
演示如何同时管理多个 ARK 服务器
"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ark_asa_manager.core import ProcessManager
import time


def example_multiple_servers():
    """示例1: 同时启动多个服务器"""
    print("=" * 60)
    print("示例1: 多服务器管理")
    print("=" * 60)
    
    pm = ProcessManager()
    
    # 定义服务器配置
    servers_config = {
        "island_server": {
            "map": "TheIsland_WP",
            "session_name": "Island_PvP",
            "port": 7777,
            "query_port": 27015,
        },
        "scorched_server": {
            "map": "ScorchedEarth_WP",
            "session_name": "Scorched_PvE",
            "port": 7778,
            "query_port": 27016,
        },
        "center_server": {
            "map": "TheCenter_WP",
            "session_name": "Center_Cluster",
            "port": 7779,
            "query_port": 27017,
        },
    }
    
    print(f"\n当前运行中的服务器数: {pm.get_running_count()}")
    print(f"运行中的服务器列表: {pm.get_all_running_servers()}\n")
    
    # 模拟启动服务器（实际应该是真实的游戏服务器）
    for server_id, config in servers_config.items():
        print(f"启动 {server_id} ({config['map']}) ...")
        print(f"  - 地图: {config['map']}")
        print(f"  - 会话名称: {config['session_name']}")
        print(f"  - 端口: {config['port']}/{config['query_port']}")
        print()
    
    print(f"总共应该启动 {len(servers_config)} 个服务器\n")


def example_server_status():
    """示例2: 检查服务器状态"""
    print("=" * 60)
    print("示例2: 服务器状态检查")
    print("=" * 60)
    
    pm = ProcessManager()
    
    server_ids = ["island_server", "scorched_server", "center_server"]
    
    print("\n服务器状态:\n")
    for server_id in server_ids:
        is_running = pm.is_running(server_id)
        pid = pm.get_pid(server_id)
        
        status = "运行中" if is_running else "已停止"
        pid_info = f"(PID: {pid})" if pid else "(无进程)"
        
        print(f"  {server_id:20} -> {status:8} {pid_info}")
    
    print(f"\n总运行数: {pm.get_running_count()}")
    print(f"运行中的服务器: {pm.get_all_running_servers()}\n")


def example_selective_stop():
    """示例3: 选择性停止服务器"""
    print("=" * 60)
    print("示例3: 选择性停止服务器")
    print("=" * 60)
    
    pm = ProcessManager()
    
    print("\n操作序列:")
    print("1. 停止 'island_server'")
    print("   pm.stop('island_server', timeout=30)")
    print()
    print("2. 检查运行中的服务器")
    print(f"   当前运行数: {pm.get_running_count()}")
    print(f"   运行列表: {pm.get_all_running_servers()}")
    print()


def example_stop_all():
    """示例4: 一次停止所有服务器"""
    print("=" * 60)
    print("示例4: 批量停止所有服务器")
    print("=" * 60)
    
    pm = ProcessManager()
    
    print("\n执行 pm.stop_all(timeout=30)")
    print("这将安全地停止所有运行中的服务器")
    print(f"\n当前运行中的服务器数: {pm.get_running_count()}")
    print(f"运行列表: {pm.get_all_running_servers()}\n")


def example_actual_usage():
    """示例5: 实际使用场景代码"""
    print("=" * 60)
    print("示例5: 实际使用场景")
    print("=" * 60)
    
    code_example = '''
from ark_asa_manager.core import ProcessManager
from pathlib import Path

# 初始化进程管理器
pm = ProcessManager()

# 启动岛屿服务器
pm.start(
    server_id="island_server",
    executable=Path(r"C:\\GameServer\\ShooterGameServer.exe"),
    args=[
        "/Map=TheIsland_WP",
        "?SessionName=Island_PvP",
        "?Port=7777",
        "?QueryPort=27015",
        "-server",
    ],
    cwd=Path(r"C:\\GameServer\\ARK-Survival-Ascended-Server")
)

# 启动焦土服务器
pm.start(
    server_id="scorched_server",
    executable=Path(r"C:\\GameServer\\ShooterGameServer.exe"),
    args=[
        "/Map=ScorchedEarth_WP",
        "?SessionName=Scorched_PvE",
        "?Port=7778",
        "?QueryPort=27016",
        "-server",
    ],
    cwd=Path(r"C:\\GameServer\\ARK-Survival-Ascended-Server")
)

# 检查状态
print(f"运行中的服务器数: {pm.get_running_count()}")
print(f"服务器列表: {pm.get_all_running_servers()}")

# 停止特定服务器
# pm.stop("island_server", timeout=30)

# 或停止所有服务器
# pm.stop_all(timeout=30)
    '''
    
    print(code_example)
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " ProcessManager 字典式多进程管理 - 使用示例 ".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    example_multiple_servers()
    print()
    
    example_server_status()
    print()
    
    example_selective_stop()
    print()
    
    example_stop_all()
    print()
    
    example_actual_usage()
    
    print("=" * 60)
    print("提示: 更多详情请查看 docs/PROCESS_MANAGER_GUIDE.md")
    print("=" * 60)
    print()
