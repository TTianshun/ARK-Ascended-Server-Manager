"""
全局常量定义
"""

# 应用信息
APP_NAME = "ARK: Survival Ascended Server Manager"
APP_USERMODEL_ID = "Ch4r0ne.ARKASAManager"
APP_VERSION = "1.0.0"

# Steam
ARK_ASA_APP_ID = 2430930  # ASA Dedicated Server AppID
STEAMCMD_ZIP_URL = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
DEFAULT_STEAMCMD_DIR = r"C:\GameServer\SteamCMD"

# 服务器默认配置
DEFAULT_SERVER_DIR = r"C:\GameServer\ARK-Survival-Ascended-Server"
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
