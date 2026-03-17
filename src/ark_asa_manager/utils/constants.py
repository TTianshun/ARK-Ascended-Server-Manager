"""
全局常量定义
"""
import os
from pathlib import Path

# 应用信息
APP_NAME = "ARK: Survival Ascended Server Manager"
APP_USERMODEL_ID = "Ch4r0ne.ARKASAManager"
APP_VERSION = "1.0.0"

# Steam
ARK_ASA_APP_ID = 2430930  # ASA Dedicated Server AppID
STEAMCMD_ZIP_URL = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"

# 默认安装路径：优先使用 %PROGRAMDATA%（通常为 C:\ProgramData），
# 避免硬编码 C:\ 导致在非 C 盘系统或无管理员权限时失败。
_GAME_ROOT = Path(os.environ.get("PROGRAMDATA") or r"C:\ProgramData") / "GameServer"
DEFAULT_STEAMCMD_DIR = str(_GAME_ROOT / "SteamCMD")

# 服务器默认配置
DEFAULT_SERVER_DIR = str(_GAME_ROOT / "ARK-Survival-Ascended-Server")
DEFAULT_MAP = "TheIsland_WP"
DEFAULT_SERVER_NAME = "default"
DEFAULT_PORT = 7777
DEFAULT_QUERY_PORT = 27015
DEFAULT_MAX_PLAYERS = 70

# RCON
DEFAULT_RCON_HOST = "127.0.0.1"
DEFAULT_RCON_PORT = 27020

# 依赖项下载
VC_REDIST_X64_URL = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
DXWEBSETUP_URL = "https://download.microsoft.com/download/1/7/1/1718CCC4-6315-4D8E-9543-8E28A4E18C4C/dxwebsetup.exe"
AMAZON_ROOT_CA1_URL = "https://www.amazontrust.com/repository/AmazonRootCA1.cer"
AMAZON_R2M02_URL = "https://crt.r2m02.amazontrust.com/r2m02.cer"

# 超时和延迟
DOWNLOAD_TIMEOUT_SEC = 180
AUTOSAVE_DEBOUNCE_MS = 700
INI_APPLY_DEBOUNCE_MS = 500
DEFAULT_SCHEDULE_TIME = "03:00"

# 地图列表
MAP_PRESETS = [
    "TheIsland_WP",
    "ScorchedEarth_WP",
    "TheCenter_WP",
    "Aberration_WP",
    "Extinction_WP",
    "Ragnarok_WP",
    "Valguero_WP",
    "LostColony_WP",
]
MAP_CUSTOM_SENTINEL = "Custom..."

# 存储目录
APPDATA_DIR_NAME = "ARK-Ascended-Server-Manager"
LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "app.log"
STAGING_DIR_NAME = "staging"
BASELINE_DIR_NAME = "baseline"
BACKUP_DIR_NAME = "backups"
SERVERS_DIR_NAME = "servers"
LOCKS_DIR_NAME = "locks"

# 配置文件
GLOBAL_CONFIG_NAME = "global.json"
LEGACY_CONFIG_NAME = "config.json"
SERVER_CONFIG_NAME = "server.json"

# 服务器 INI 文件（相对于服务器安装目录）
from pathlib import Path as _Path
GAMEUSERSETTINGS_REL = _Path(r"ShooterGame\Saved\Config\WindowsServer\GameUserSettings.ini")
GAME_INI_REL = _Path(r"ShooterGame\Saved\Config\WindowsServer\Game.ini")

# 服务器进程自动重启
AUTO_RESTART_EXIT_CODES: frozenset = frozenset({3})
AUTO_RESTART_DELAY_SEC: float = 5.0

# DirectX 遗留 DLL 列表（用于 DirectX 安装检测）
DIRECTX_LEGACY_DLLS = [
    "d3dx9_43.dll",
    "d3dx10_43.dll",
    "d3dx11_43.dll",
    "d3dcompiler_43.dll",
    "xinput1_3.dll",
]
