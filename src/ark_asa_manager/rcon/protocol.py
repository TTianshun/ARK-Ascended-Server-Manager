"""
RCON协议实现（Source RCON Protocol）
"""
import socket
import struct
from typing import Optional, Tuple


class RCONProtocol:
    """RCON协议处理"""
    
    # RCON包类型常量
    SERVERDATA_AUTH = 3
    SERVERDATA_AUTH_RESPONSE = 2
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_RESPONSE_VALUE = 0

    # 合理的单包大小上限，防止恶意/错误数据撑爆内存
    _MAX_PACKET_SIZE = 4096
    
    def __init__(self, host: str = "127.0.0.1", port: int = 27020):
        self.host = host
        self.port = port
        self._socket: Optional[socket.socket] = None
        self._authenticated = False
        self._request_id = 0
    
    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def connect(self, timeout: int = 10) -> bool:
        """连接到RCON服务器"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(timeout)
            sock.connect((self.host, self.port))
            self._socket = sock
            return True
        except Exception as e:
            print(f"RCON连接失败: {e}")
            # 确保连接失败时套接字被正确关闭，避免文件描述符泄漏
            try:
                sock.close()
            except Exception:
                pass
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
        """
        发送认证包并验证服务器响应。
        Source RCON 协议：服务器先回复一个空 RESPONSE_VALUE，
        再回复 AUTH_RESPONSE；若密码错误则 AUTH_RESPONSE 的 ID 为 -1。
        """
        if not self._socket:
            return False
        try:
            req_id = self._next_request_id()
            self._send_packet(self.SERVERDATA_AUTH, password, req_id)

            # 读取最多两个响应包，寻找 AUTH_RESPONSE
            for _ in range(2):
                resp_id, resp_type, _ = self._receive_packet()
                if resp_type == self.SERVERDATA_AUTH_RESPONSE:
                    if resp_id == -1:
                        print("RCON认证失败：密码错误")
                        return False
                    self._authenticated = True
                    return True

            print("RCON认证失败：未收到认证响应")
            return False
        except Exception as e:
            print(f"RCON认证异常: {e}")
            self._authenticated = False
            return False
    
    def execute_command(self, command: str) -> Optional[str]:
        """执行命令并返回响应文本"""
        if not self._socket or not self._authenticated:
            return None
        try:
            req_id = self._next_request_id()
            self._send_packet(self.SERVERDATA_EXECCOMMAND, command, req_id)
            _, _, response_text = self._receive_packet()
            return response_text
        except Exception as e:
            print(f"RCON命令执行失败: {e}")
            # 连接可能已断开，重置认证状态
            self._authenticated = False
            return None

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------

    def _next_request_id(self) -> int:
        """生成递增的请求 ID（循环，避免溢出）"""
        self._request_id = (self._request_id % 0x7FFFFFFF) + 1
        return self._request_id

    def _send_packet(self, packet_type: int, text: str, request_id: int) -> None:
        """按 Source RCON 格式打包并发送数据包"""
        if not self._socket:
            raise RuntimeError("未连接")
        body = text.encode('utf-8')
        # payload = ID(4) + Type(4) + body + null(1) + null(1)
        payload = struct.pack("<ii", request_id, packet_type) + body + b'\x00\x00'
        # 前缀 4 字节表示 payload 长度
        packet = struct.pack("<i", len(payload)) + payload
        self._socket.sendall(packet)

    def _recv_exactly(self, n: int) -> bytes:
        """循环接收，直到恰好得到 n 个字节"""
        data = b''
        while len(data) < n:
            chunk = self._socket.recv(n - len(data))  # type: ignore[union-attr]
            if not chunk:
                raise ConnectionError("RCON 连接已断开")
            data += chunk
        return data

    def _receive_packet(self) -> Tuple[int, int, str]:
        """
        接收一个完整 RCON 数据包。
        返回 (request_id, packet_type, body_text)。
        """
        if not self._socket:
            raise RuntimeError("未连接")

        # 读取 4 字节长度字段
        size_data = self._recv_exactly(4)
        size = struct.unpack("<i", size_data)[0]

        if size < 8 or size > self._MAX_PACKET_SIZE:
            raise ValueError(f"无效的 RCON 包大小: {size}")

        # 读取完整 payload
        payload = self._recv_exactly(size)
        resp_id = struct.unpack("<i", payload[0:4])[0]
        resp_type = struct.unpack("<i", payload[4:8])[0]
        # body 在 ID(4)+Type(4) 之后，去掉末尾两个 null 字节
        body_text = payload[8:-2].decode('utf-8', errors='ignore') if len(payload) > 10 else ""

        return resp_id, resp_type, body_text

    # ------------------------------------------------------------------
    # 向后兼容的旧接口（供外部已有调用使用）
    # ------------------------------------------------------------------

    def _send_command(self, command_type: int, text: str) -> None:
        self._send_packet(command_type, text, self._next_request_id())

    def _receive_response(self) -> str:
        _, _, body = self._receive_packet()
        return body
