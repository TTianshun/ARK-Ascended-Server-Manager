"""
RCON协议实现
"""
import socket
import struct
import time
from typing import Optional


class RCONProtocol:
    """RCON协议处理"""
    
    # RCON包类型
    SERVERDATA_AUTH = 3
    SERVERDATA_AUTH_RESPONSE = 2
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_RESPONSE_VALUE = 0
    
    def __init__(self, host: str = "127.0.0.1", port: int = 27020):
        self.host = host
        self.port = port
        self._socket: Optional[socket.socket] = None
        self._authenticated = False
    
    def connect(self, timeout: int = 10) -> bool:
        """连接到RCON服务器"""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(timeout)
            self._socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"RCON连接失败: {e}")
            self._socket = None
            return False
    
    def disconnect(self) -> None:
        """断开连接"""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
        self._authenticated = False
    
    def authenticate(self, password: str) -> bool:
        """认证"""
        try:
            self._send_command(self.SERVERDATA_AUTH, password)
            return True
        except Exception as e:
            print(f"RCON认证失败: {e}")
            return False
    
    def execute_command(self, command: str) -> Optional[str]:
        """执行命令"""
        try:
            self._send_command(self.SERVERDATA_EXECCOMMAND, command)
            response = self._receive_response()
            return response
        except Exception as e:
            print(f"RCON命令执行失败: {e}")
            return None
    
    def _send_command(self, command_type: int, text: str) -> None:
        """发送命令"""
        if not self._socket:
            raise RuntimeError("未连接")
        
        request_id = 1
        body = text.encode('utf-8')
        length = struct.calcsize("II") + len(body) + 2
        
        packet = struct.pack("<II", length, request_id)
        packet += struct.pack("<I", command_type)
        packet += body + b'\x00\x00'
        
        self._socket.sendall(packet)
    
    def _receive_response(self) -> str:
        """接收响应"""
        if not self._socket:
            raise RuntimeError("未连接")
        
        # 接收包头
        header = self._socket.recv(4)
        if len(header) < 4:
            return ""
        
        length = struct.unpack("<I", header)[0]
        
        # 接收包体
        body = b''
        while len(body) < length:
            chunk = self._socket.recv(length - len(body))
            if not chunk:
                break
            body += chunk
        
        # 解析响应
        if len(body) >= 8:
            response_text = body[8:-2].decode('utf-8', errors='ignore')
            return response_text
        
        return ""
