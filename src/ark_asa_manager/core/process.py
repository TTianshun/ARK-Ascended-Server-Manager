"""
进程管理
"""
import subprocess
import time
import os
from typing import Optional, List
from pathlib import Path


class ProcessManager:
    """服务器进程管理"""
    
    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._pid: Optional[int] = None
    
    def is_running(self) -> bool:
        """检查进程是否运行中"""
        if self._pid is None:
            return False
        try:
            os.kill(self._pid, 0)
            return True
        except OSError:
            return False
    
    def start(
        self,
        executable: Path,
        args: Optional[List[str]] = None,
        cwd: Optional[Path] = None
    ) -> bool:
        """
        启动进程
        
        Args:
            executable: 可执行文件路径
            args: 命令行参数
            cwd: 工作目录
        
        Returns:
            成功返回True
        """
        try:
            if self.is_running():
                return False
            
            cmd = [str(executable)]
            if args:
                cmd.extend(args)
            
            # Windows下隐藏窗口
            kwargs = {}
            if os.name == 'nt':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            if cwd:
                kwargs['cwd'] = str(cwd)
            
            self._process = subprocess.Popen(cmd, **kwargs)
            self._pid = self._process.pid
            return True
        except Exception as e:
            print(f"启动进程失败: {e}")
            return False
    
    def stop(self, timeout: int = 30) -> bool:
        """
        停止进程
        
        Args:
            timeout: 等待超时（秒）
        
        Returns:
            成功返回True
        """
        if not self.is_running():
            return True
        
        try:
            if self._process:
                self._process.terminate()
                try:
                    self._process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait()
            return True
        except Exception as e:
            print(f"停止进程失败: {e}")
            return False
    
    def get_pid(self) -> Optional[int]:
        """获取进程ID"""
        return self._pid
