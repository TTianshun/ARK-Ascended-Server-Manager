"""
存储管理
"""
from pathlib import Path
from typing import Optional


class StorageManager:
    """存储区域管理"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self._ensure_structure()
    
    def _ensure_structure(self) -> None:
        """确保存储目录结构"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建主要子目录
        dirs = ["servers", "staging", "baseline", "backups", "logs", "locks"]
        for dir_name in dirs:
            (self.base_dir / dir_name).mkdir(exist_ok=True)
    
    def get_servers_dir(self) -> Path:
        """获取服务器目录"""
        return self.base_dir / "servers"
    
    def get_staging_dir(self, server_name: str) -> Path:
        """获取临时编辑目录"""
        path = self.base_dir / "staging" / server_name
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_baseline_dir(self, server_name: str) -> Path:
        """获取基线目录"""
        path = self.base_dir / "baseline" / server_name
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_backup_dir(self, server_name: str) -> Path:
        """获取备份目录"""
        path = self.base_dir / "backups" / server_name
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_logs_dir(self) -> Path:
        """获取日志目录"""
        return self.base_dir / "logs"
    
    def get_locks_dir(self) -> Path:
        """获取锁文件目录"""
        return self.base_dir / "locks"
