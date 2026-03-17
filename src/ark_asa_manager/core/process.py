"""
进程管理
"""
import subprocess
import threading
import os
from typing import Optional, List, Dict
from pathlib import Path


class ProcessManager:
    """多服务器进程管理 - 支持同时运行多个服务器"""
    
    def __init__(self):
        # 字典式管理：server_id -> Popen 对象
        self._processes: Dict[str, subprocess.Popen] = {}
        # 字典式管理：server_id -> PID
        self._pids: Dict[str, int] = {}
        # 可重入锁，保护所有对 _processes/_pids 的并发访问
        self._lock = threading.RLock()
    
    def is_running(self, server_id: str) -> bool:
        """
        检查特定服务器进程是否运行中
        
        Args:
            server_id: 服务器唯一标识
            
        Returns:
            运行中返回True，否则返回False
        """
        with self._lock:
            if server_id not in self._pids:
                return False
            try:
                pid = self._pids[server_id]
                os.kill(pid, 0)
                return True
            except OSError:
                # 进程已终止，清理数据
                self._cleanup(server_id)
                return False
    
    def start(
        self,
        server_id: str,
        executable: Path,
        args: Optional[List[str]] = None,
        cwd: Optional[Path] = None
    ) -> bool:
        """
        启动指定服务器的进程
        
        Args:
            server_id: 服务器唯一标识
            executable: 可执行文件路径
            args: 命令行参数
            cwd: 工作目录
        
        Returns:
            成功返回True，服务器已运行则返回False
        """
        with self._lock:
            if self.is_running(server_id):
                print(f"服务器 {server_id} 已在运行，启动失败")
                return False
            
            try:
                cmd = [str(executable)]
                if args:
                    cmd.extend(args)
                
                # Windows下隐藏窗口
                kwargs: dict = {}
                if os.name == 'nt':
                    kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                if cwd:
                    kwargs['cwd'] = str(cwd)
                
                process = subprocess.Popen(cmd, **kwargs)
                self._processes[server_id] = process
                self._pids[server_id] = process.pid
                print(f"服务器 {server_id} 启动成功，PID: {process.pid}")
                return True
            except Exception as e:
                print(f"启动服务器 {server_id} 失败: {e}")
                # 确保失败时清理任何可能遗留的状态
                self._cleanup(server_id)
                return False
    
    def stop(self, server_id: str, timeout: int = 30) -> bool:
        """
        停止指定服务器的进程
        
        Args:
            server_id: 服务器唯一标识
            timeout: 等待超时（秒）
        
        Returns:
            成功返回True
        """
        with self._lock:
            if not self.is_running(server_id):
                return True
            
            try:
                process = self._processes.get(server_id)
                if process is not None:
                    process.terminate()
                    try:
                        process.wait(timeout=timeout)
                        print(f"服务器 {server_id} 已安全关闭")
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                        print(f"服务器 {server_id} 被强制关闭")
                self._cleanup(server_id)
                return True
            except Exception as e:
                print(f"停止服务器 {server_id} 失败: {e}")
                return False
    
    def stop_all(self, timeout: int = 30) -> bool:
        """
        停止所有运行中的服务器
        
        Args:
            timeout: 单个服务器的等待超时（秒）
        
        Returns:
            所有服务器都成功停止返回True
        """
        with self._lock:
            server_ids = list(self._pids.keys())
        all_success = True
        for server_id in server_ids:
            if not self.stop(server_id, timeout):
                all_success = False
        return all_success
    
    def get_pid(self, server_id: str) -> Optional[int]:
        """
        获取指定服务器的进程ID
        
        Args:
            server_id: 服务器唯一标识
            
        Returns:
            进程ID，如果不存在则返回None
        """
        with self._lock:
            return self._pids.get(server_id)
    
    def get_all_running_servers(self) -> List[str]:
        """
        获取所有运行中的服务器ID列表
        
        Returns:
            服务器ID列表
        """
        with self._lock:
            server_ids = list(self._pids.keys())
        running = []
        for server_id in server_ids:
            if self.is_running(server_id):
                running.append(server_id)
        return running
    
    def get_running_count(self) -> int:
        """
        获取运行中的服务器数量
        
        Returns:
            运行中的服务器数量
        """
        return len(self.get_all_running_servers())
    
    def _cleanup(self, server_id: str) -> None:
        """
        清理指定服务器的进程数据（调用方须持有 _lock）
        
        Args:
            server_id: 服务器唯一标识
        """
        self._processes.pop(server_id, None)
        self._pids.pop(server_id, None)
