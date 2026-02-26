"""
服务器配置和状态模型
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .enums import ServerStatus, RCONStatus


@dataclass
class RCONConfig:
    """RCON配置"""
    host: str = "127.0.0.1"
    port: int = 27020
    password: str = ""
    enabled: bool = True


@dataclass
class ServerConfig:
    """服务器配置"""
    name: str
    server_dir: Path
    map_name: str = "TheIsland_WP"
    port: int = 7777
    query_port: int = 27015
    max_players: int = 70
    server_password: str = ""
    admin_password: str = ""
    rcon: RCONConfig = field(default_factory=RCONConfig)
    
    # 高级配置
    use_battleye: bool = True
    enable_crossplay: bool = True
    difficulty: float = 1.0
    day_cycle_speed: float = 1.0
    
    # 存储路径
    staging_dir: Optional[Path] = None
    baseline_dir: Optional[Path] = None
    backup_dir: Optional[Path] = None
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "server_dir": str(self.server_dir),
            "map_name": self.map_name,
            "port": self.port,
            "query_port": self.query_port,
            "max_players": self.max_players,
            "server_password": self.server_password,
            "admin_password": self.admin_password,
            "rcon": {
                "host": self.rcon.host,
                "port": self.rcon.port,
                "password": self.rcon.password,
                "enabled": self.rcon.enabled,
            },
            "use_battleye": self.use_battleye,
            "enable_crossplay": self.enable_crossplay,
            "difficulty": self.difficulty,
            "day_cycle_speed": self.day_cycle_speed,
        }


@dataclass
class ServerState:
    """服务器运行状态"""
    status: ServerStatus = ServerStatus.STOPPED
    rcon_status: RCONStatus = RCONStatus.DISCONNECTED
    process_id: Optional[int] = None
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # 统计信息
    uptime_seconds: int = 0
    last_restart: Optional[datetime] = None
    crash_count: int = 0
