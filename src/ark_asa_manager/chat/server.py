"""
LACC WebSocket 中继服务器

实现 LACC (Lily and Azure's Cluster Chat) 的 WebSocket 中继协议：
- 客户端通过 handshake 认证 (name, token, version, clusterKey)
- 认证后的 ChatMessage JSON 在所有连接间广播
- 支持从管理器注入 admin 消息
"""

import asyncio
import json
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Optional

import websockets
from websockets.server import ServerConnection

_logger = logging.getLogger(__name__)

HANDSHAKE_REQUIRED_FIELDS = ("name", "token", "version")
HANDSHAKE_OPTIONAL_FIELDS = ("clusterKey",)
CURRENT_PAYLOAD_VERSION = 3
MAX_MESSAGE_HISTORY = 500

LACC_MOD_ID = "1056780"


@dataclass
class ConnectedClient:
    """已连接的 LACC 客户端信息"""
    name: str
    cluster_key: str
    version: int
    connected_at: float = field(default_factory=time.time)


@dataclass
class ChatMessage:
    """LACC ChatMessage 结构"""
    send_mode: int = 0
    map_name: str = ""
    sender_name: str = ""
    sender_tribe_id: int = 0
    sender_tribe_name: str = ""
    sender_id: str = ""
    message: str = ""
    time_received: float = 0.0
    is_admin: bool = False
    cluster_key: str = ""
    platform_player_name: str = ""
    map_colour: str = ""
    raw_json: str = ""

    def to_json(self) -> str:
        return json.dumps({
            "sendMode": self.send_mode,
            "mapName": self.map_name,
            "senderName": self.sender_name,
            "senderTribeId": self.sender_tribe_id,
            "senderTribeName": self.sender_tribe_name,
            "senderId": self.sender_id,
            "message": self.message,
            "timeReceived": self.time_received,
            "isAdmin": self.is_admin,
            "clusterKey": self.cluster_key,
            "platformPlayerName": self.platform_player_name,
            "mapColour": self.map_colour,
        }, ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "ChatMessage":
        data = json.loads(raw)

        def get_field(keys, default=""):
            for k in keys:
                if k in data and data[k]:
                    return data[k]
            return default

        time_recv = get_field(["timeReceived", "TimeReceived", "time_received"], 0.0)
        if not time_recv or time_recv <= 0:
            time_recv = time.time()

        return cls(
            send_mode=get_field(["sendMode", "SendMode", "send_mode"], 0),
            map_name=get_field(["mapName", "MapName", "map_name", "map"], ""),
            sender_name=get_field(["senderName", "SenderName", "sender_name", "playerName", "PlayerName", "player_name"], ""),
            sender_tribe_id=get_field(["senderTribeId", "SenderTribeId", "sender_tribe_id", "tribeId", "TribeId"], 0),
            sender_tribe_name=get_field(["senderTribeName", "SenderTribeName", "sender_tribe_name", "tribeName", "TribeName"], ""),
            sender_id=get_field(["senderId", "SenderId", "sender_id", "playerId", "PlayerId"], ""),
            message=get_field(["message", "Message", "msg", "content", "Content", "text", "Text"], ""),
            time_received=time_recv,
            is_admin=get_field(["isAdmin", "IsAdmin", "is_admin", "admin", "Admin"], False),
            cluster_key=get_field(["clusterKey", "ClusterKey", "cluster_key"], ""),
            platform_player_name=get_field(["platformPlayerName", "PlatformPlayerName", "platform_player_name"], ""),
            map_colour=get_field(["mapColour", "MapColour", "map_colour", "mapColor", "MapColor"], ""),
            raw_json=raw,
        )


class LACCWebSocketServer:
    """
    LACC WebSocket 中继服务器。

    在独立线程中运行 asyncio 事件循环，管理 LACC 客户端连接，
    广播 ChatMessage，并通过回调将事件传递给 UI 层。
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        token: str = "",
        cluster_key: str = "",
        on_message: Optional[Callable[[ChatMessage], None]] = None,
        on_connect: Optional[Callable[[str], None]] = None,
        on_disconnect: Optional[Callable[[str], None]] = None,
    ):
        self.host = host
        self.port = port
        self.token = token
        self.cluster_key = cluster_key

        self._on_message = on_message
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect

        self._clients: Dict[ServerConnection, ConnectedClient] = {}
        self._lock = threading.Lock()
        self._message_history: Deque[ChatMessage] = deque(maxlen=MAX_MESSAGE_HISTORY)

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._server: Optional[asyncio.Task] = None
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def get_connected_clients(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "name": c.name,
                    "cluster_key": c.cluster_key,
                    "version": c.version,
                    "connected_at": c.connected_at,
                }
                for c in self._clients.values()
            ]

    def get_message_history(self) -> List[ChatMessage]:
        with self._lock:
            return list(self._message_history)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._running:
            _logger.warning("LACC WebSocket 服务器已在运行中")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="LACC-WS-Server"
        )
        self._thread.start()
        _logger.info("LACC WebSocket 服务器已启动 (%s:%d)", self.host, self.port)

    def stop(self) -> None:
        if not self._running:
            return

        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        self._thread = None
        self._loop = None
        with self._lock:
            self._clients.clear()
        _logger.info("LACC WebSocket 服务器已停止")

    def update_config(self, port: int, token: str, cluster_key: str) -> None:
        self.port = port
        self.token = token
        self.cluster_key = cluster_key

    # ------------------------------------------------------------------
    # Admin message injection
    # ------------------------------------------------------------------

    def send_admin_message(self, message_text: str, sender_name: str = "Admin") -> None:
        """从管理器向所有已连接客户端广播管理员消息"""
        if not self._running or not self._loop:
            _logger.warning("WebSocket 服务器未运行，无法发送消息")
            return

        msg = ChatMessage(
            send_mode=0,
            map_name="管理器",
            sender_name=sender_name,
            sender_tribe_id=0,
            sender_tribe_name="",
            sender_id="admin",
            message=message_text,
            time_received=time.time(),
            is_admin=True,
            cluster_key=self.cluster_key,
            platform_player_name=sender_name,
            map_colour="255,165,0,255",
        )

        with self._lock:
            self._message_history.append(msg)

        if self._on_message:
            try:
                self._on_message(msg)
            except Exception:
                pass

        asyncio.run_coroutine_threadsafe(
            self._broadcast(msg.to_json(), exclude=None), self._loop
        )

    # ------------------------------------------------------------------
    # Internal asyncio loop
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except Exception as e:
            if self._running:
                _logger.error("LACC WebSocket 服务器异常: %s", e)
        finally:
            try:
                self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            except Exception:
                pass
            try:
                self._loop.close()
            except Exception:
                pass
            self._running = False

    async def _serve(self) -> None:
        server = await websockets.serve(
            self._handler,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10,
        )
        try:
            while self._running:
                await asyncio.sleep(0.5)
        finally:
            server.close()
            await server.wait_closed()

    async def _handler(self, websocket: ServerConnection) -> None:
        client_id = None
        try:
            handshake_raw = await asyncio.wait_for(websocket.recv(), timeout=10)
            _logger.info(
                "[LACC][HANDSHAKE] 收到握手消息: %s",
                handshake_raw[:500] if len(handshake_raw) > 500 else handshake_raw
            )
            valid, result, info = self._validate_handshake(handshake_raw)

            if not valid:
                _logger.warning("Handshake 失败: %s", result)
                try:
                    await websocket.send(result)
                    await websocket.close(1008, result)
                except Exception:
                    pass
                return

            _logger.info(
                "[LACC][HANDSHAKE] 验证成功: name=%s, token=%s, version=%s, clusterKey=%s",
                info.get("name"), info.get("token"), info.get("version"), info.get("clusterKey")
            )
            await websocket.send("success")
            client_id = info["name"]

            client = ConnectedClient(
                name=info["name"],
                cluster_key=info.get("clusterKey", ""),
                version=info.get("version", 0),
            )
            with self._lock:
                self._clients[websocket] = client

            _logger.info("客户端已连接: %s (cluster: %s, version: %s)", client.name, client.cluster_key, client.version)
            if self._on_connect:
                try:
                    self._on_connect(client.name)
                except Exception:
                    pass

            async for raw_message in websocket:
                _logger.info(
                    "[LACC][RAW] 收到原始消息 (来自 %s): %s",
                    client.name,
                    raw_message[:1000] if len(raw_message) > 1000 else raw_message
                )

                try:
                    raw_data = json.loads(raw_message)
                    _logger.info(
                        "[LACC][KEYS] 消息包含的字段: %s",
                        list(raw_data.keys()) if isinstance(raw_data, dict) else type(raw_data).__name__
                    )
                    _logger.info("[LACC][DATA] 完整解析数据: %s", raw_data)
                except json.JSONDecodeError:
                    pass

                try:
                    msg = ChatMessage.from_json(raw_message)
                except (json.JSONDecodeError, Exception) as e:
                    _logger.warning("无法解析消息: %s (raw=%s)", e, raw_message[:500])
                    continue

                _logger.info(
                    "[LACC][PARSED] sendMode=%s, map=%s, sender=%s, tribeName=%s, "
                    "senderId=%s, message=%s, isAdmin=%s, clusterKey=%s, platformPlayer=%s",
                    msg.send_mode, msg.map_name, msg.sender_name, msg.sender_tribe_name,
                    msg.sender_id, msg.message, msg.is_admin, msg.cluster_key, msg.platform_player_name
                )

                with self._lock:
                    self._message_history.append(msg)

                if self._on_message:
                    try:
                        self._on_message(msg)
                    except Exception as e:
                        _logger.error("on_message 回调异常: %s", e)

                await self._broadcast(raw_message, exclude=websocket)
                _logger.info(
                    "[LACC][CHAT] [%s] %s: %s",
                    msg.map_name or "(无地图)",
                    msg.sender_name or "(无发送者)",
                    msg.message or "(空消息)"
                )

        except asyncio.TimeoutError:
            _logger.warning("客户端 handshake 超时")
        except websockets.exceptions.ConnectionClosed as e:
            _logger.debug("客户端断开连接: %s", e)
        except Exception as e:
            _logger.error("处理客户端时出错: %s", e)
        finally:
            with self._lock:
                removed = self._clients.pop(websocket, None)
            if removed:
                _logger.info("客户端已断开: %s", removed.name)
                if self._on_disconnect:
                    try:
                        self._on_disconnect(removed.name)
                    except Exception:
                        pass

    def _validate_handshake(self, raw):
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as e:
            _logger.warning("Handshake JSON 解析失败: %s (raw=%r)", e, raw[:200] if raw else raw)
            return False, "fail_server", {}

        if not isinstance(data, dict):
            _logger.warning("Handshake 数据不是 dict: %s", type(data).__name__)
            return False, "fail_server", {}

        missing = [f for f in HANDSHAKE_REQUIRED_FIELDS if f not in data]
        if missing:
            _logger.warning("Handshake 缺少必要字段: %s (收到的字段: %s)", missing, list(data.keys()))
            return False, "fail_server", {}

        if self.token and str(data.get("token", "")) != self.token:
            _logger.warning("Handshake token 不匹配 (客户端: %s)", data.get("name", "?"))
            return False, "bad_auth", {}

        if self.cluster_key and str(data.get("clusterKey", "")) != self.cluster_key:
            _logger.warning("Handshake clusterKey 不匹配 (客户端: %s)", data.get("name", "?"))
            return False, "bad_auth", {}

        return True, "success", data

    async def _broadcast(
        self, message: str, exclude: Optional[ServerConnection]
    ) -> None:
        with self._lock:
            targets = [
                ws for ws in self._clients if ws is not exclude
            ]
        for ws in targets:
            try:
                await ws.send(message)
            except Exception:
                pass
