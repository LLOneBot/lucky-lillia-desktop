"""常量定义"""

NPM_PACKAGES = {
    "pmhq": "pmhq-dist-win-x64",
    "llbot": "llonebot-dist",
    "node": "llonebot-node-win-x64",
    "ffmpeg": "llonebot-ffmpeg-win-x64",
    "app": "lucky-lillia-desktop-win-x64"
}

GITHUB_REPOS = {
    "llbot": "LLOneBot/LLOneBot",
    "app": "LLOneBot/lucky-lillia-desktop",
    "pmhq": "linyuchen/pmhq",
}

DEFAULT_CONFIG = {
    "qq_path": "",
    "pmhq_path": "bin/pmhq/pmhq-win-x64.exe",
    "llbot_path": "bin/llbot/llbot.js",
    "node_path": "bin/llbot/node.exe",
    "auto_start_pmhq": False,
    "auto_start_llbot": False,
    "auto_start_bot": False,
    "auto_login_qq": "",
    "headless": False,
    "minimize_to_tray_on_start": False,
    "log_level": "info",
    "log_save_enabled": True,
    "log_retention_seconds": 86400,
    "theme_mode": "dark",
    "window_width": 1200.0,
    "window_height": 800.0,
    "close_to_tray": None
}

APP_NAME = "LLBotDesktop"
CONFIG_FILE = "app_settings.json"

PMHQ_DIR = "bin/pmhq"
PMHQ_EXECUTABLE = "pmhq-win-x64.exe"

LLBOT_DIR = "bin/llbot"
LLBOT_MAIN = "llbot.js"

MAX_LOG_LINES = 1000
LOG_REFRESH_INTERVAL_MS = 100

UPDATE_CHECK_TIMEOUT = 10

GITHUB_MIRRORS = [
    "https://ghfast.top/https://github.com/",
    "https://gh-proxy.com/https://github.com/",
    "https://mirror.ghproxy.com/https://github.com/",
    "https://github.com/",
]

NPM_REGISTRY_MIRRORS = [
    "https://registry.npmjs.org",
    "https://registry.npmmirror.com",
]

RESOURCE_MONITOR_INTERVAL = 3.0

DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
DEFAULT_THEME = "light"

TRAY_TOOLTIP = "LLBot"
CLOSE_TO_TRAY_DEFAULT = False
MINIMIZE_TO_TRAY_ON_START_DEFAULT = False

QQ_DOWNLOAD_URL = "https://dldir1v6.qq.com/qqfile/qq/QQNT/c50d6326/QQ9.9.22.40768_x64.exe"
