"""
存储管理
"""
from pathlib import Path

from ..utils.constants import (
    BACKUP_DIR_NAME,
    BASELINE_DIR_NAME,
    LOCKS_DIR_NAME,
    LOG_DIR_NAME,
    SERVERS_DIR_NAME,
    STAGING_DIR_NAME,
)


class StorageManager:
    """存储区域管理"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self._ensure_structure()
    
    def _ensure_structure(self) -> None:
        """确保存储目录结构"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Legacy 对齐：servers 根目录 + logs + 全局 locks
        dirs = [SERVERS_DIR_NAME, LOG_DIR_NAME, LOCKS_DIR_NAME]
        for dir_name in dirs:
            (self.base_dir / dir_name).mkdir(exist_ok=True)
    
    def get_servers_dir(self) -> Path:
        """获取服务器目录"""
        return self.base_dir / SERVERS_DIR_NAME

    def get_server_dir(self, server_id: str) -> Path:
        path = self.get_servers_dir() / server_id
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_staging_dir(self, server_name: str) -> Path:
        """获取临时编辑目录"""
        path = self.get_server_dir(server_name) / STAGING_DIR_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_baseline_dir(self, server_name: str) -> Path:
        """获取基线目录"""
        path = self.get_server_dir(server_name) / BASELINE_DIR_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_backup_dir(self, server_name: str) -> Path:
        """获取备份目录"""
        path = self.get_server_dir(server_name) / BACKUP_DIR_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_logs_dir(self) -> Path:
        """获取日志目录"""
        return self.base_dir / LOG_DIR_NAME
    
    def get_locks_dir(self) -> Path:
        """获取锁文件目录"""
        return self.base_dir / LOCKS_DIR_NAME

    def get_server_locks_dir(self, server_id: str) -> Path:
        path = self.get_server_dir(server_id) / LOCKS_DIR_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path
