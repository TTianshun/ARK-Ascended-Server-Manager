"""
RCON客户端
"""
from typing import Optional
from .protocol import RCONProtocol


class RCONClient:
    """RCON客户端"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 27020, password: str = ""):
        self.host = host
        self.port = port
        self.password = password
        self._protocol = RCONProtocol(host, port)
        self._connected = False
    
    def connect(self) -> bool:
        """连接和认证"""
        if not self._protocol.connect():
            return False
        
        if not self._protocol.authenticate(self.password):
            self._protocol.disconnect()
            return False
        
        self._connected = True
        return True
    
    def disconnect(self) -> None:
        """断开连接"""
        self._protocol.disconnect()
        self._connected = False
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    def execute(self, command: str) -> Optional[str]:
        """执行命令"""
        if not self._connected:
            return None
        
        return self._protocol.execute_command(command)
    
    def get_players(self) -> Optional[str]:
        """获取玩家列表"""
        return self.execute("ListPlayers")
    
    def get_info(self) -> Optional[str]:
        """获取服务器信息"""
        return self.execute("GetGameModeName")
    
    def save(self) -> Optional[str]:
        """保存游戏"""
        return self.execute("SaveWorld")
