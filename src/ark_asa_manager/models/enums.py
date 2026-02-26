"""
枚举类型定义
"""
from enum import Enum


class ServerStatus(Enum):
    """服务器状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class Platform(Enum):
    """系统平台"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


class ProcessState(Enum):
    """进程状态"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


class RCONStatus(Enum):
    """RCON连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
